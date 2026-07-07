import logging

from app.ai.base import AIProvider

logger = logging.getLogger(__name__)


class FallbackAIProvider(AIProvider):
    """Decorator/Composite: try a primary AIProvider, fall back to a
    secondary one if the primary raises.

    Both sides are plain `AIProvider`s, so this composes cleanly with
    `RetryingAIProvider` — each side can already carry its own retry policy
    without either provider knowing a fallback exists. If the fallback also
    fails, its exception propagates unchanged.
    """

    def __init__(self, primary: AIProvider, fallback: AIProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    async def generate(self, prompt: str) -> str:
        try:
            return await self._primary.generate(prompt)
        except Exception:
            logger.warning(
                "Primary AI provider failed; falling back to secondary provider.",
                exc_info=True,
            )
            return await self._fallback.generate(prompt)
