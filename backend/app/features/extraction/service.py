from datetime import date
from typing import Annotated

from fastapi import Depends

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.features.extraction.normalizer import normalize
from app.features.extraction.parser import parse_json_array
from app.features.extraction.prompts import build_extraction_prompt
from app.features.extraction.schemas import ExtractedTaskDTO


class ExtractionService:
    """Thin orchestration: build prompt -> call the AI provider -> parse -> normalize.

    Depends only on the AIProvider abstraction (injected) — never a concrete
    SDK, never the database. MeetingService is what persists the result; this
    class has no knowledge of meetings or tasks as DB rows.
    """

    def __init__(self, ai_provider: AIProvider) -> None:
        self._ai_provider = ai_provider

    async def extract(self, notes: str, *, reference_date: date) -> list[ExtractedTaskDTO]:
        prompt = build_extraction_prompt(notes, reference_date)
        raw_response = await self._ai_provider.generate(prompt)
        raw_items = parse_json_array(raw_response)
        return normalize(raw_items)


def get_extraction_service(
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
) -> ExtractionService:
    return ExtractionService(ai_provider)
