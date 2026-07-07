import logging

from app.ai.base import AIProvider
from app.ai.fallback import FallbackAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.retry import RetryingAIProvider
from app.core.config import settings
from app.core.constants.messages import UNSUPPORTED_AI_PROVIDER_MESSAGE_TEMPLATE
from app.core.enums import AIProviderName
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_PROVIDERS: dict[AIProviderName, type[AIProvider]] = {
    AIProviderName.GEMINI: GeminiProvider,
    AIProviderName.GROQ: GroqProvider,
}

_FALLBACK_PROVIDER_NAME = AIProviderName.GROQ


def get_ai_provider() -> AIProvider:
    """FastAPI dependency: construct the configured AIProvider, retry-wrapped,
    with an automatic fallback to Groq if the primary provider fails.

    Adding a new primary provider (OpenAI, Claude, Ollama, ...) means adding
    one class plus one `_PROVIDERS` entry — nothing else in the application
    changes. If `GROQ_API_KEY` isn't configured, the fallback is silently
    omitted rather than breaking the primary provider.
    """
    primary_cls = _PROVIDERS.get(settings.ai_provider)
    if primary_cls is None:
        raise ExternalServiceError(
            UNSUPPORTED_AI_PROVIDER_MESSAGE_TEMPLATE.format(provider=settings.ai_provider)
        )
    primary: AIProvider = RetryingAIProvider(primary_cls())

    fallback = _build_fallback_provider()
    if fallback is None:
        return primary
    return FallbackAIProvider(primary, fallback)


def _build_fallback_provider() -> AIProvider | None:
    """Build the retry-wrapped Groq fallback, or None if unavailable/redundant."""
    if settings.ai_provider == _FALLBACK_PROVIDER_NAME:
        return None  # Groq is already the primary; no separate fallback needed

    fallback_cls = _PROVIDERS[_FALLBACK_PROVIDER_NAME]
    try:
        return RetryingAIProvider(fallback_cls())
    except ExternalServiceError:
        logger.warning(
            "Fallback provider %r is not configured; continuing without a fallback.",
            _FALLBACK_PROVIDER_NAME.value,
        )
        return None
