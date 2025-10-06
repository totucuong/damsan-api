# Codebase Overview

## Runtime Entry Points
- `main.py` instantiates the FastAPI app, includes the `v1` routers, and exposes a `/health` check.
- `pyproject.toml` exposes the console script `damsan = "damsan:main"`, which still targets `src/damsan/__init__.py:main` for CLI experiments.

## HTTP Layer (`src/damsan_api`)
- `config.py` defines `Settings` via `pydantic-settings`, pulling `.env` values for model selection and prompt paths.
- `services/answer_service.py` adapts `Damsan.answer`, handling configuration defaults and article filtering.
- `api/v1/answer.py` declares the `POST /v1/answer` endpoint backed by the service and maps exceptions to HTTP responses.
- `api/v1/schemas.py` stores the Pydantic request/response models.
- Each new directory ships with a README stub describing its role.

## Core Package (`src/damsan`)
- `damsan.py` defines the `Damsan` class that orchestrates retrieval, summarisation, and synthesis.
- `pubmed_engine.py` wraps PubMed search and LLM prompt orchestration via `PubMedNeuralRetriever`.
- `bm25.py` provides BM25-based reranking helpers for long article lists.
- `utils/prompt_compiler.py` loads the prompt architecture JSON and turns it into LangChain prompt objects.

## Prompt Assets
- `prompts/PubMed/Architecture_1/master.json` describes the prompt architecture consumed by `PromptArchitecture`.
- `prompts/PubMed/Architecture_1/task_*_prompt.json` and `task_*_sys.json` store individual user/system messages referenced by the architecture.

## Research & Experiments
- `notebooks/pubmed.py` is a playground notebook for experimenting with the retrieval pipeline.

## Configuration & Environment
- `.env` provides `PROMPT_PATH`, `MODEL`, `OPENAI_API_KEY`, and `EMAIL` for both CLI and API runs.
- `uv.lock` records the resolved dependency set for reproducible installs.

## Tooling & Development
- Prefer `uv` for dependency management: `uv pip install --editable .[dev]` keeps the lockfile in sync, and `uv pip sync --extra dev` reproduces environments.
- To run the API locally: `uv run uvicorn main:app --reload`. The service expects the `.env` keys above to be present.
- Create a virtual environment with `python3.13 -m venv .venv && source .venv/bin/activate` when working without `uv` helpers.
- Formatting and linting rely on `black`, `ruff`, and `flake8` from the `dev` extras.
