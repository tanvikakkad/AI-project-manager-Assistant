import logging
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.constants.messages import INTERNAL_ERROR_MESSAGE, REQUEST_VALIDATION_ERROR_MESSAGE
from app.core.responses import ErrorDetail, error_response

logger = logging.getLogger(__name__)

# Keys to drop from each raw error dict before it goes into a JSON response.
# `ctx` may contain the raw exception instance a custom validator raised
# (Pydantic's `ValueError`-wrapping mechanism), which is not JSON-serializable.
_NON_SERIALIZABLE_ERROR_KEYS = ("ctx", "url")


def _sanitize_validation_errors(errors: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in error.items() if key not in _NON_SERIALIZABLE_ERROR_KEYS}
        for error in errors
    ]


class AppException(Exception):
    """Base class for all expected, application-level errors.

    Every subclass carries the HTTP status and error code it should map to,
    so routers never need their own try/except blocks.
    """

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found"


class ValidationError(AppException):
    status_code = 422
    error_code = "validation_error"


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict"


class ExternalServiceError(AppException):
    """Raised when a downstream dependency (e.g. the AI provider) fails."""

    status_code = 502
    error_code = "external_service_error"


async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            ErrorDetail(code=exc.error_code, message=exc.message, details=exc.details)
        ).model_dump(),
    )


async def _handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Ensures FastAPI's own request-body validation errors (raised before any
    route or service code runs) still return our `APIErrorResponse` shape,
    not FastAPI's default `{"detail": [...]}` — one error envelope, everywhere.
    """
    app_exc = ValidationError(
        REQUEST_VALIDATION_ERROR_MESSAGE,
        details={"errors": _sanitize_validation_errors(exc.errors())},
    )
    return await _handle_app_exception(request, app_exc)


async def _handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content=error_response(
            ErrorDetail(code="internal_error", message=INTERNAL_ERROR_MESSAGE)
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register every exception handler in one place."""
    app.add_exception_handler(AppException, _handle_app_exception)
    app.add_exception_handler(RequestValidationError, _handle_request_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_exception)
