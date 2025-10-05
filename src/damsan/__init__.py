from .damsan import Damsan
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    clinfo_ai = Damsan(
        prompt_file_path=os.getenv("PROMPT_PATH", ""),
        model=os.getenv("MODEL", ""),
        engine="PubMed",
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        email=os.getenv("EMAIL", ""),
        verbose=True,
    )
    articles, queries = clinfo_ai.retrive_articles(
        "What is the role of IL-17 in cancer?"
    )
    print("articles:", articles)
    print("queries:", queries)
