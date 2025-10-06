"""Tests for the v1 answer endpoint."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from damsan_api.api.v1.answer import _get_answer_service
from damsan_api.services.exceptions import AnswerUnavailableError
from main import app


@contextmanager
def override_service(service: Any):
    original = getattr(_get_answer_service, "_service", None)
    _get_answer_service._service = service  # type: ignore[attr-defined]
    try:
        yield
    finally:
        if original is None:
            delattr(_get_answer_service, "_service")
        else:
            _get_answer_service._service = original  # type: ignore[attr-defined]


class StubService:
    """Stub implementation that returns canned responses."""

    def __init__(self, response: Dict[str, Any]):
        self._response = response

    def answer(self, **_: Any) -> Dict[str, Any]:
        return self._response


class FailingService:
    """Stub service that raises an availability error."""

    def __init__(self, exc: Exception):
        self._exc = exc

    def answer(self, **_: Any) -> Dict[str, Any]:
        raise self._exc


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_answer_returns_payload(client: TestClient) -> None:
    response_payload = {
        "synthesis": "Clinical summary",
        "article_summaries": ["a"],
        "irrelevant_articles": [],
        "queries": ["query"],
    }

    with override_service(StubService(response_payload)):
        response = client.post(
            "/v1/answer",
            json={"question": "What is IL-17?"},
        )

    assert response.status_code == 200
    assert response.json() == response_payload


def test_answer_handles_service_failure(client: TestClient) -> None:
    with override_service(FailingService(AnswerUnavailableError("downstream"))):
        response = client.post(
            "/v1/answer",
            json={"question": "What is IL-17?"},
        )

    assert response.status_code == 503
    body = response.json()
    assert body["detail"] == "downstream"
