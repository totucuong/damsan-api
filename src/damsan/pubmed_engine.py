import re
import sys
import string
import time
import openai
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from Bio import Entrez
from Bio.Entrez import efetch, esearch
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from .utils.prompt_compiler import PromptArchitecture
import logging

logger = logging.getLogger(__name__)
sys.path.append(str(Path(__file__).resolve().parent))


def subtract_n_years(date_str: str, n: int = 20) -> str:
    date = datetime.strptime(date_str, "%Y/%m/%d")  # Parse the given date string
    new_year = date.year - n  # Subtract n years

    # Check if the resulting year is a leap year
    is_leap_year = (new_year % 4 == 0 and new_year % 100 != 0) or new_year % 400 == 0

    # Adjust the day value if necessary
    new_day = date.day
    if date.month == 2 and date.day == 29 and not is_leap_year:
        new_day = 28

    # Create a new date with the updated year, month, and day
    new_date = datetime(new_year, date.month, new_day)

    # Format the new date to the desired format (YYYY/MM/DD)
    formatted_date = new_date.strftime("%Y/%m/%d")
    return formatted_date


class PubMedNeuralRetriever:
    def __init__(
        self,
        architecture_path: str,
        temperature: float = 0.5,
        model: str = "gpt-3.5-turbo",
        verbose: bool = True,
        open_ai_key: str = "",
        email: str = "",
        wait: int = 3,
    ):

        self.model = model
        self.verbose = verbose
        self.architecture = PromptArchitecture(
            architecture_path=architecture_path, verbose=verbose
        )
        self.temperature = temperature
        self.open_ai_key = open_ai_key
        self.email = email
        self.time_out = 61
        self.delay = 2
        self.wait = wait

        if self.verbose:
            self.architecture.print_architecture()

        openai.api_key = self.open_ai_key

    def query_api(
        self,
        model: str,
        prompt: list,
        temperature: float,
        max_tokens: int = 1024,
        n: int = 1,
    ) -> str:

        chat = ChatOpenAI(
            temperature=temperature,
            model=model,
            n=n,
        )

        return chat(prompt).text()

    def generate_pubmed_query(
        self,
        question: str,
        max_tokens: int = 1024,
    ) -> str:
        user_prompt = self.architecture.get_prompt("pubmed_query_prompt", "template")
        system_prompt = self.architecture.get_prompt(
            "pubmed_query_prompt", "system"
        ).format()
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_prompt)
        human_message_prompt = HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                template=user_prompt.format(question="{question}"),
                input_variables=["question"],
            )
        )
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        chat_prompt = chat_prompt.format_prompt(question=question).to_messages()

        result = self.query_api(
            model=self.model,
            prompt=chat_prompt,
            temperature=self.temperature,
            max_tokens=max_tokens,
            n=1,
        )

        return result

    def search_pubmed(
        self,
        question: str,
        num_results: int = 10,
        num_query_attempts: int = 1,
        verbose: bool = False,
        restriction_date=None,
    ) -> Tuple[list[str], list[str]]:

        Entrez.email = self.email
        search_ids = set()
        search_queries = set()

        for _ in range(num_query_attempts):
            pubmed_query = self.generate_pubmed_query(question)

            if restriction_date:
                if self.verbose:
                    print(f"Date Restricted to : {restriction_date}")
                lower_limit = subtract_n_years(restriction_date)
                pubmed_query = (
                    pubmed_query + f" AND {lower_limit}:{restriction_date}[dp]"
                )

            if verbose:
                print("*" * 10)
                print(f"Generated pubmed query: {pubmed_query}\n")

            search_queries.add(pubmed_query)
            search_results = esearch(
                db="pubmed", term=pubmed_query, retmax=num_results, sort="relevance"
            )
            try:
                search_response = Entrez.read(search_results)
                if (
                    search_response
                    and isinstance(search_response, dict)
                    and "IdList" in search_response
                ):
                    retrieved_ids = search_response["IdList"]
                    search_ids = search_ids.union(retrieved_ids)

                    if len(retrieved_ids) == 0:
                        logger.warning(
                            f"Failed to retrieve IDs for query: {pubmed_query}"
                        )

                    if verbose:
                        print(f"Retrieved {len(retrieved_ids)} IDs")
                        print(retrieved_ids)
                else:
                    logger.warning(
                        f"No IdList found in response for query: {pubmed_query}"
                    )

            except Exception as e:
                logger.error(f"Error retrieving IDs: {str(e)}")

        return list(search_queries), list(search_ids)

    def fetch_article_data(self, article_ids: List[str]):
        articles = efetch(db="pubmed", id=article_ids, rettype="xml")
        # article_data = Entrez.read(articles)["PubmedArticle"]
        article_data = []
        search_response = Entrez.read(articles)
        if (
            search_response
            and isinstance(search_response, dict)
            and "PubmedArticle" in search_response
        ):
            article_data = search_response["PubmedArticle"]

        return article_data

    def is_article_relevant(
        self,
        article_text: str,
        question: str,
        max_tokens: int = 512,
        is_reconstruction=False,
    ):
        user_prompt = self.architecture.get_prompt("relevance_prompt", "template")
        system_prompt = self.architecture.get_prompt(
            "relevance_prompt", "system"
        ).format()

        logger.debug(f"User prompt: {user_prompt}")
        logger.debug(f"System prompt: {system_prompt}")

        if is_reconstruction:
            message_ = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt.format(
                        question=question, article_text=article_text
                    ),
                },
            ]
            return message_
        else:
            system_message_prompt = SystemMessagePromptTemplate.from_template(
                system_prompt
            )
            human_message_prompt = HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    template=user_prompt.format(
                        question="{question}", article_text="{article_text}"
                    ),
                    input_variables=["question", "article_text"],
                )
            )

            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )
            chat_prompt = chat_prompt.format_prompt(
                question=question, article_text=article_text
            ).to_messages()

            result = self.query_api(
                model=self.model,
                prompt=chat_prompt,
                temperature=self.temperature,
                max_tokens=max_tokens,
                n=1,
            )

            first_word = result.split()[0].strip(string.punctuation).lower()
            return first_word not in {"no", "n"}

    def construct_citation(self, article):
        if (
            len(article["PubmedData"]["ReferenceList"]) == 0
            or len(article["PubmedData"]["ReferenceList"][0]["Reference"]) == 0
        ):
            return self.generate_ama_citation(article)
        else:
            try:
                citation = article["PubmedData"]["ReferenceList"][0]["Reference"][0][
                    "Citation"
                ]
                return citation
            except IndexError as err:
                print(f"IndexError: {err}")

    def generate_ama_citation(self, article):
        try:
            authors = article["MedlineCitation"]["Article"]["AuthorList"]
            author_names = ", ".join(
                [f"{author['LastName']} {author['Initials']}" for author in authors]
            )
        except KeyError:
            author_names = ""

        try:
            title = article["MedlineCitation"]["Article"]["ArticleTitle"]
        except KeyError:
            title = ""

        try:
            journal = article["MedlineCitation"]["Article"]["Journal"]["Title"]
        except KeyError:
            journal = ""

        try:
            pub_date = article["PubmedData"]["History"][0]["Year"]
        except KeyError:
            pub_date = ""

        try:
            volume = article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ]
        except KeyError:
            volume = ""

        try:
            issue = article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Issue"
            ]
        except KeyError:
            issue = ""

        try:
            pages = article["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"]
        except KeyError:
            pages = ""

        return (
            f"{author_names}. {title}. {journal}. {pub_date};{volume}({issue}):{pages}."
        )

    def write_results_to_file(self, filename, ama_citation, summary, append=True):
        mode = "a" if append else "w"
        with open(filename, mode, encoding="utf-8") as f:
            f.write(f"Citation: {ama_citation}\n")
            f.write(f"{summary}")
            f.write("\n###\n\n")

    def reconstruct_abstract(self, abstract_elements):
        reconstructed_abstract = ""
        for element in abstract_elements:
            label = element.attributes.get("Label", "")
            if reconstructed_abstract:
                reconstructed_abstract += "\n\n"

            if label:
                reconstructed_abstract += f"{label}:\n"
            reconstructed_abstract += str(element)
        return reconstructed_abstract

    def summarize_study(
        self,
        article_text,
        question,
    ) -> str:
        system_prompt = self.architecture.get_prompt(
            "summarization_prompt", "system"
        ).format()

        user_prompt = self.architecture.get_prompt("summarization_prompt", "template")
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_prompt)
        human_message_prompt = HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                template=user_prompt.format(
                    question="{question}", article_text="{article_text}"
                ),
                input_variables=["question", "article_text"],
            )
        )

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        chat_prompt = chat_prompt.format_prompt(
            question=question, article_text=article_text
        ).to_messages()
        result = self.query_api(
            model=self.model,
            prompt=chat_prompt,
            temperature=self.temperature,
            max_tokens=1024,
            n=1,
        )

        return result

    def process_article(self, article, question):
        try:
            abstract = article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]
            abstract = self.reconstruct_abstract(abstract)
            article_is_relevant = self.is_article_relevant(abstract, question)
            citation = self.construct_citation(article)
            if self.verbose:
                print(citation)
                print("~" * 10 + f"\n{abstract}")
                print("~" * 10 + f"\nArticle is relevant? = {article_is_relevant}")

            title = article["MedlineCitation"]["Article"]["ArticleTitle"]
            url = (
                f"https://pubmed.ncbi.nlm.nih.gov/"
                f"{article['MedlineCitation']['PMID']}/"
            )
            article_json = {
                "title": title,
                "url": url,
                "abstract": abstract,
                "citation": citation,
                "is_relevant": article_is_relevant,
                "PMID": article["MedlineCitation"]["PMID"],
            }

            if article_is_relevant:
                summary = self.summarize_study(article_text=abstract, question=question)
                article_json["summary"] = summary

            return article_json
        except KeyError as err:
            if "PMID" in article["MedlineCitation"].keys():
                print(
                    f"Could not find {err} for article with PMID = "
                    f"{article['MedlineCitation']['PMID']}"
                )
            else:
                print("Error retrieving article data:", err)
            return None
        except ValueError as err:
            print("Error: ", err)
            return None

    def summarize_each_article(self, articles, question, num_workers=8):
        relevant_article_summaries = []
        irrelevant_article_summaries = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(self.process_article, article, question)
                for article in articles
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    print(
                        "Error processing article. Server is probably overloaded. "
                        "waiting 10 seconds",
                        e,
                    )
                    time.sleep(20)
                    print("Lets try again")
                    result = future.result()
                if result is not None:
                    if result["is_relevant"]:
                        relevant_article_summaries.append(result)
                    else:
                        irrelevant_article_summaries.append(result)

        return relevant_article_summaries, irrelevant_article_summaries

    def build_citations_and_summaries(
        self, article_summaries: dict, with_url: bool = False
    ) -> tuple:
        article_summaries_with_citations = []
        citations = []
        for i, summary in enumerate(article_summaries):
            citation = re.sub(r"\n", "", summary["citation"])
            article_summaries_with_citations.append(
                f"[{i+1}] Source: {citation}\n\n\n {summary['summary']}"
            )
            citation_with_index = f"[{i+1}] {citation}"
            if with_url:
                citation_with_index = (
                    f"<li><a href=\"{summary['url']}\" target=\"_blank\">"
                    f" {citation_with_index}</a></li>"
                )

            citations.append(citation_with_index)
        article_summaries_with_citations = (
            "\n\n--------------------------------------------------------------\n\n"
        ).join(article_summaries_with_citations)

        citations = "\n".join(citations)

        if with_url:
            citations = f"<ul>{citations}</ul>"

        return article_summaries_with_citations, citations

    def synthesize_all_articles(
        self,
        summaries,
        question,
        with_url=False,
    ):
        article_summaries_str, citations = self.build_citations_and_summaries(
            article_summaries=summaries, with_url=with_url
        )

        system_prompt = self.architecture.get_prompt(
            "synthesize_prompt", "system"
        ).format()
        user_prompt = self.architecture.get_prompt("synthesize_prompt", "template")
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_prompt)
        human_message_prompt = HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                template=user_prompt.format(
                    question="{question}",
                    article_summaries_str="{article_summaries_str}",
                ),
                input_variables=["question", "article_summaries_str"],
            )
        )

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        chat_prompt = chat_prompt.format_prompt(
            question=question, article_summaries_str=article_summaries_str
        ).to_messages()
        result = self.query_api(
            model=self.model,
            prompt=chat_prompt,
            temperature=self.temperature,
            max_tokens=1024,
            n=1,
        )
        if with_url:
            result = result + "\n\n" + "References:\n" + citations
        return result

    def PIPE_LINE(self, question: str):
        pubmed_queries, article_ids = self.search_pubmed(
            question, num_results=4, num_query_attempts=1
        )
        articles = self.fetch_article_data(article_ids)
        article_summaries, irrelevant_articles = self.summarize_each_article(
            articles, question
        )
        synthesis = self.synthesize_all_articles(article_summaries, question)

        return (
            synthesis,
            article_summaries,
            irrelevant_articles,
            articles,
            article_ids,
            pubmed_queries,
        )
