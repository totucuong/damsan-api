"""FastAPI router exposing the `Damsan.answer` functionality."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import get_settings
from ...services.answer_service import AnswerService
from ...services.exceptions import AnswerUnavailableError
from .schemas import AnswerRequest, AnswerResponse

router = APIRouter(prefix="/v1", tags=["answer"])


def _get_answer_service() -> AnswerService:
    """Return a cached answer service instance."""

    if not hasattr(_get_answer_service, "_service"):
        settings = get_settings()
        _get_answer_service._service = AnswerService(settings=settings)  # type: ignore[attr-defined]
    return _get_answer_service._service  # type: ignore[attr-defined]


@router.post("/answer", response_model=AnswerResponse)
def post_answer(
    payload: AnswerRequest,
    service: AnswerService = Depends(_get_answer_service),
) -> AnswerResponse:
    """Generate an answer for the supplied clinical question."""

    try:
        result = service.answer(
            question=payload.question,
            bm25=payload.bm25,
            restriction_date=payload.restriction_date,
            return_articles=payload.return_articles,
        )
    except AnswerUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return AnswerResponse.model_validate(result)
