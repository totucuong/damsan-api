"""Pydantic models for the v1 answer endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    """Payload accepted by the `/answer` endpoint."""

    question: str = Field(..., min_length=1, description="Clinical question to answer")
    bm25: bool = Field(default=False, description="Enable BM25 reranking")
    restriction_date: Optional[date] = Field(
        default=None,
        description="Upper bound (YYYY-MM-DD) for included articles",
    )
    return_articles: Optional[bool] = Field(
        default=None,
        description="Override default article return behaviour",
    )


class AnswerResponse(BaseModel):
    """Structured response returned to clients."""

    synthesis: Any
    article_summaries: Optional[List[Any]] = None
    irrelevant_articles: Optional[List[Any]] = None
    queries: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "synthesis": "Summary of the clinical evidence...",
                "article_summaries": [
                    {"pmid": "12345", "summary": "Key findings..."}
                ],
                "irrelevant_articles": [],
                "queries": ["IL-17 cancer role"],
            }
        }
    }
