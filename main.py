"""FastAPI application entrypoint for the damsan API."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from damsan_api.api.v1.answer import router as answer_router
from damsan_api.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Validate configuration when the application starts up."""

    try:
        settings = get_settings()
        settings.ensure_prompt_path()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Startup validation skipped: %s", exc)
    yield


app = FastAPI(title="damsan-api", version="0.1.0", lifespan=lifespan)
app.include_router(answer_router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    """Simple health endpoint."""

    return {"status": "ok"}
