from .pubmed_engine import PubMedNeuralRetriever
from .bm25 import bm25_ranked


class ClinfoAI:
    def __init__(
        self,
        architecture_path,
        llm: str = "gpt-3.5-turbo",
        engine: str = "PubMed",
        openai_key: str = "YOUR API TOKEN",
        email: str = "YOUR EMAIL",
        dense_search: bool = False,
        verbose: bool = False,
    ) -> None:

        self.engine = engine
        self.llm = llm
        self.email = email
        self.openai_key = openai_key
        self.verbose = verbose
        self.architecture_path = architecture_path
        self.dense_search = dense_search
        self.init_engine()

    def init_engine(self):
        if self.engine == "PubMed":

            self.NEURAL_RETRIVER = PubMedNeuralRetriever(
                architecture_path=self.architecture_path,
                model=self.llm,
                verbose=self.verbose,
                debug=False,
                open_ai_key=self.openai_key,
                email=self.email,
            )
            print("PubMed Retriever Initialized")
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
                print(
                    f"Sorry, we weren't able to find any articles in {self.engine} "
                    f"relevant to your question. Please try again."
                )
                return [], []

            articles = self.NEURAL_RETRIVER.fetch_article_data(article_ids)
            if self.verbose:
                print(
                    f"Retrieved {len(articles)} articles. Identifying the relevant ones"
                    f"and summarizing them (this may take a minute)"
                )
            return articles, queries
        except Exception as error:
            print(f"Internal Service Error, {self.engine} might be down: {error}")
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
                print("Using BM25 to rank articles")
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
