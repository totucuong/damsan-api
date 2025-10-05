"""Clinical information retrieval orchestration for the damsan package."""

import logging

from .pubmed_engine import PubMedNeuralRetriever
from .bm25 import bm25_ranked


logger = logging.getLogger(__name__)


class ClinfoAI:
    def __init__(
        self,
        architecture_path,
        llm: str = "gpt-3.5-turbo",
        engine: str = "PubMed",
        openai_key: str = "YOUR API TOKEN",
        email: str = "YOUR EMAIL",
        verbose: bool = False,
    ) -> None:

        self.engine = engine
        self.llm = llm
        self.email = email
        self.openai_key = openai_key
        self.verbose = verbose
        self.architecture_path = architecture_path
        self.init_engine()

    def init_engine(self):
        if self.engine == "PubMed":
            self.NEURAL_RETRIVER = PubMedNeuralRetriever(
                architecture_path=self.architecture_path,
                model=self.llm,
                verbose=self.verbose,
                open_ai_key=self.openai_key,
                email=self.email,
            )
            logger.info("PubMed Retriever initialized")
        else:
            raise Exception("Invalid Engine")

        return "OK"

    def retrive_articles(self, question, restriction_date=None):
        try:
            queries, article_ids = self.NEURAL_RETRIVER.search_pubmed(
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

            articles = self.NEURAL_RETRIVER.fetch_article_data(article_ids)
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
        article_summaries, irrelevant_articles = (
            self.NEURAL_RETRIVER.summarize_each_article(articles, question)
        )
        return article_summaries, irrelevant_articles

    def synthesis_task(
        self, article_summaries, question, USE_BM25=False, with_url=True
    ):
        if USE_BM25:
            if len(article_summaries) > 21:
                logger.info("Using BM25 to rank articles")
                corpus = [article["abstract"] for article in article_summaries]
                article_summaries = bm25_ranked(
                    list_to_oganize=article_summaries,
                    corpus=corpus,
                    query=question,
                    n=20,
                )

        synthesis = self.NEURAL_RETRIVER.synthesize_all_articles(
            article_summaries, question, with_url=with_url
        )
        return synthesis

    def forward(self, question, restriction_date=None, return_articles=True):
        articles, queries = self.retrive_articles(question, restriction_date)
        article_summaries, irrelevant_articles = self.summarize_relevant(
            articles=articles, question=question
        )
        synthesis = self.synthesis_task(article_summaries, question)
        out = dict()
        out["synthesis"] = synthesis
        if return_articles:
            out["article_summaries"] = article_summaries
            out["irrelevant_articles"] = irrelevant_articles
            out["queries"] = queries

        return out
