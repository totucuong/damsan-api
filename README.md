# damsan-api

FastAPI wrapper for the damsan clinical retrieval pipeline.

## Quickstart

1. Install dependencies with `uv pip sync --extra dev` (or `pip install -e .[dev]` in a Python 3.13 virtualenv).
2. Provide `.env` values for `PROMPT_PATH`, `MODEL`, `OPENAI_API_KEY`, and `EMAIL`.
3. Launch the API with `uv run uvicorn main:app --reload` and call `POST /v1/answer` with a JSON payload containing `question`.

Run `pytest` to execute the new HTTP tests.
