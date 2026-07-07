from typing import Any

from pydantic import BaseModel


class APIResponse[T](BaseModel):
    """Uniform success envelope returned by every endpoint."""

    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class APIErrorResponse(BaseModel):
    """Uniform error envelope returned by every endpoint, regardless of layer."""

    error: ErrorDetail


def success_response[T](data: T) -> APIResponse[T]:
    return APIResponse(data=data)


def error_response(detail: ErrorDetail) -> APIErrorResponse:
    return APIErrorResponse(error=detail)
