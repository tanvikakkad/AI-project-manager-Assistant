from groq import AsyncGroq

from app.ai.base import AIProvider
from app.ai.constants import EXTRACTION_TEMPERATURE
from app.core.config import settings
from app.core.constants.messages import EMPTY_AI_RESPONSE_MESSAGE, GROQ_API_KEY_MISSING_MESSAGE
from app.core.exceptions import ExternalServiceError


class GroqProvider(AIProvider):
    """Talks to the Groq SDK only — same one-method contract as every other
    provider. Used both as a fully standalone `AIProvider` (`AI_PROVIDER=groq`)
    and as the automatic fallback when the primary provider is unavailable.

    Unlike `GeminiProvider`, this does not force `response_format` json mode:
    Groq's (OpenAI-compatible) strict JSON-object mode expects a top-level
    JSON *object*, but our shared extraction prompt asks for a top-level JSON
    *array* — forcing that mode here would risk the API rejecting valid
    output. Correctness instead relies on the shared prompt plus the
    extraction parser's tolerant JSON-array extraction, which already handles
    prose/markdown wrapping from any provider.
    """

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ExternalServiceError(GROQ_API_KEY_MISSING_MESSAGE)
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    async def generate(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=EXTRACTION_TEMPERATURE,
        )
        text = response.choices[0].message.content
        if not text:
            raise ExternalServiceError(EMPTY_AI_RESPONSE_MESSAGE)
        return text
