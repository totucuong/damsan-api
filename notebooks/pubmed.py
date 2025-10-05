import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    from damsan.clinfoai import Damsan

    from dotenv import load_dotenv
    import os

    load_dotenv()
    from damsan.pubmed_engine import PubMedNeuralRetriever

    # clinfo_ai = ClinfoAI(
    #         architecture_path=os.getenv("PROMPT_PATH", ""),
    #         llm=os.getenv("MODEL", ""),
    #         engine="PubMed",
    #         openai_key=os.getenv("OPENAI_API_KEY", ""),
    #         email=os.getenv("EMAIL", ""),
    #         verbose=True,
    #     )
    # articles, queries = clinfo_ai.retrive_articles("What is the role of IL-17 in cancer?")
    # print("articles:", articles)
    # print("queries:", queries)
    return PubMedNeuralRetriever, os


@app.cell
def _(PubMedNeuralRetriever, os):
    retriever = PubMedNeuralRetriever(
        email="totucuong@gmail.com",
        architecture_path=os.getenv("PROMPT_PATH", ""),
        model=os.getenv("MODEL", ""),
        open_ai_key=os.getenv("OPENAI_API_KEY", ""),
    )
    return (retriever,)


@app.cell
def _(retriever):
    synthesis, article_summaries, _, _, _, _ = retriever.answer(
        "What is the role of IL6 in immune system"
    )
    return article_summaries, synthesis


@app.cell
def _(synthesis):
    print(synthesis)
    return


@app.cell
def _(article_summaries):
    print(article_summaries[0]["url"])
    return


@app.cell
def _(article_summaries):
    print(article_summaries[0]["abstract"])
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
