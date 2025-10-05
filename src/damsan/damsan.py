"""Clinical information retrieval orchestration for the damsan package."""

import logging

from .pubmed_engine import PubMedNeuralRetriever
from .bm25 import bm25_ranked


logger = logging.getLogger(__name__)


class Damsan:
    def __init__(
        self,
        prompt_file_path,
        model: str = "gpt-5",
        engine: str = "PubMed",
        openai_api_key: str = "YOUR API TOKEN",
        email: str = "YOUR EMAIL",
        verbose: bool = False,
    ) -> None:

        self.engine = engine
        self.llm = model
        self.email = email
        self.openai_api_key = openai_api_key
        self.verbose = verbose
        self.prompt_file_path = prompt_file_path
        self.init_engine()

    def init_engine(self):
        if self.engine == "PubMed":
            self.retriever = PubMedNeuralRetriever(
                prompt_file_path=self.prompt_file_path,
                model=self.llm,
                verbose=self.verbose,
                openai_api_key=self.openai_api_key,
                email=self.email,
            )
            logger.info("PubMed Retriever initialized")
        else:
            raise Exception("Invalid Engine")

        return "OK"

    def retrive_articles(self, question, restriction_date=None):
        try:
            queries, article_ids = self.retriever.search_pubmed(
                question=question,
                num_results=16,
                num_query_attempts=3,
                restriction_date=restriction_date,
            )
            if (len(queries) == 0) or (len(article_ids) == 0):
                logger.warning(
                    "No relevant articles found in %s for the provided question",
                    self.engine,
                )
                return [], []

            articles = self.retriever.fetch_article_data(article_ids)
            if self.verbose:
                logger.info(
                    "Retrieved %s articles. Identifying the relevant ones and "
                    "summarizing them (this may take a minute)",
                    len(articles),
                )
            return articles, queries
        except Exception as error:
            logger.exception("Internal service error; %s may be unavailable", error)
            return [], []

    def summarize_relevant(self, articles, question):
        article_summaries, irrelevant_articles = self.retriever.summarize_each_article(
            articles, question
        )
        return article_summaries, irrelevant_articles

    def synthesis_task(self, article_summaries, question, bm25=False, with_url=True):
        if bm25:
            if len(article_summaries) > 21:
                logger.info("Using BM25 to rank articles")
                corpus = [article["abstract"] for article in article_summaries]
                article_summaries = bm25_ranked(
                    list_to_oganize=article_summaries,
                    corpus=corpus,
                    query=question,
                    n=20,
                )

        synthesis = self.retriever.synthesize_all_articles(
            article_summaries, question, with_url=with_url
        )
        return synthesis

    def answer(
        self, question, bm25=False, restriction_date=None, return_articles=True
    ) -> dict:
        """Answer a question using the specified retrieval and synthesis methods.

        Parameters
        ----------
        question : str
            The question to answer.
        bm25 : bool, optional
            Whether to use BM25 ranking, by default False
        restriction_date : str, optional
            A date to restrict the search, by default None
        return_articles : bool, optional
            Whether to return the retrieved articles, by default True

        Returns
        -------
        dict
            The result containing synthesis, article summaries, irrelevant articles,
            and queries.
        """
        articles, queries = self.retrive_articles(question, restriction_date)
        article_summaries, irrelevant_articles = self.summarize_relevant(
            articles=articles, question=question
        )
        synthesis = self.synthesis_task(article_summaries, question, bm25=bm25)
        result = dict()
        result["synthesis"] = synthesis
        if return_articles:
            result["article_summaries"] = article_summaries
            result["irrelevant_articles"] = irrelevant_articles
            result["queries"] = queries

        return result
