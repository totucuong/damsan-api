"""Service layer that adapts `Damsan.answer` for HTTP usage."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from damsan.damsan import Damsan

from ..config import Settings
from .exceptions import AnswerUnavailableError


class AnswerService:
    """Coordinates calls into the `Damsan` retrieval pipeline."""

    def __init__(self, settings: Settings, damsan: Optional[Damsan] = None) -> None:
        self._settings = settings
        self._damsan = damsan or self._build_damsan()

    def _build_damsan(self) -> Damsan:
        prompt_path = str(self._settings.ensure_prompt_path())
        return Damsan(
            prompt_file_path=prompt_path,
            model=self._settings.model_name,
            openai_api_key=self._settings.openai_api_key,
            email=self._settings.email,
            verbose=False,
        )

    @property
    def damsan(self) -> Damsan:
        """Expose the underlying `Damsan` instance."""

        return self._damsan

    def answer(
        self,
        *,
        question: str,
        bm25: bool = False,
        restriction_date: Optional[date] = None,
        return_articles: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Call the `Damsan.answer` method and normalise its response."""

        effective_return_articles = (
            self._settings.return_articles if return_articles is None else return_articles
        )
        restriction_date_str = (
            restriction_date.strftime("%Y/%m/%d") if restriction_date else None
        )

        try:
            payload = self.damsan.answer(
                question=question,
                bm25=bm25,
                restriction_date=restriction_date_str,
                return_articles=effective_return_articles,
            )
        except Exception as exc:  # pragma: no cover - surfaced through HTTP layer
            raise AnswerUnavailableError(str(exc)) from exc

        return self._filter_articles(payload, effective_return_articles)

    def _filter_articles(self, payload: Dict[str, Any], include_articles: bool) -> Dict[str, Any]:
        """Remove article keys when they are not requested."""

        if include_articles:
            return payload

        return {key: value for key, value in payload.items() if key == "synthesis"}
