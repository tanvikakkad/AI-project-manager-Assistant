from google import genai
from google.genai import types

from app.ai.base import AIProvider
from app.ai.constants import EXTRACTION_TEMPERATURE
from app.core.config import settings
from app.core.constants.messages import EMPTY_AI_RESPONSE_MESSAGE, GEMINI_API_KEY_MISSING_MESSAGE
from app.core.exceptions import ExternalServiceError


class GeminiProvider(AIProvider):
    """Talks to the Gemini SDK only.

    Knows nothing about prompts, task/meeting shape, retry policy, or JSON
    parsing — purely "text in, text out." `response_mime_type="application/
    json"` steers the model toward valid JSON without this class knowing
    *what* JSON shape is expected; that stays the caller's concern.
    """

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ExternalServiceError(GEMINI_API_KEY_MISSING_MESSAGE)
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=EXTRACTION_TEMPERATURE,
                response_mime_type="application/json",
            ),
        )
        if not response.text:
            raise ExternalServiceError(EMPTY_AI_RESPONSE_MESSAGE)
        return response.text
