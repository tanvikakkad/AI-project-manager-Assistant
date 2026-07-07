from app.core.exceptions import ValidationError


class AIExtractionError(ValidationError):
    """Raised when the AI provider's response isn't parseable JSON at all."""

    error_code = "ai_extraction_error"


class InvalidLLMOutputError(ValidationError):
    """Raised when parsed JSON doesn't match the expected task shape."""

    error_code = "invalid_llm_output"
