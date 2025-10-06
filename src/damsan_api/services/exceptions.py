"""Custom exceptions raised by application services."""


class AnswerServiceError(Exception):
    """Base exception for answer service errors."""


class AnswerUnavailableError(AnswerServiceError):
    """Raised when the answer pipeline fails unexpectedly."""
