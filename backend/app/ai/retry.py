import asyncio
import logging

from app.ai.base import AIProvider
from app.core.constants.messages import AI_PROVIDER_EXHAUSTED_MESSAGE_TEMPLATE
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_DEFAULT_ATTEMPTS = 3
_DEFAULT_BASE_DELAY_SECONDS = 1.0


class RetryingAIProvider(AIProvider):
    """Decorator adding bounded retry-with-backoff around any AIProvider.

    Retry policy is defined exactly once here and applies uniformly to every
    current and future provider — a new provider never reimplements its own
    retry/timeout handling.
    """

    def __init__(
        self,
        provider: AIProvider,
        *,
        attempts: int = _DEFAULT_ATTEMPTS,
        base_delay_seconds: float = _DEFAULT_BASE_DELAY_SECONDS,
    ) -> None:
        self._provider = provider
        self._attempts = attempts
        self._base_delay_seconds = base_delay_seconds

    async def generate(self, prompt: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self._attempts + 1):
            try:
                return await self._provider.generate(prompt)
            except Exception as exc:  # noqa: BLE001 - re-raised as ExternalServiceError below
                last_error = exc
                logger.warning(
                    "AI provider call failed (attempt %s/%s): %s",
                    attempt,
                    self._attempts,
                    exc,
                )
                if attempt < self._attempts:
                    await asyncio.sleep(self._base_delay_seconds * attempt)

        raise ExternalServiceError(
            AI_PROVIDER_EXHAUSTED_MESSAGE_TEMPLATE.format(attempts=self._attempts)
        ) from last_error
