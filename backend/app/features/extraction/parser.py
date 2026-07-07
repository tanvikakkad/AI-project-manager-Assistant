import json
import re
from typing import Any

from app.core.constants.messages import AI_RESPONSE_NOT_ARRAY_MESSAGE, AI_RESPONSE_NOT_JSON_MESSAGE
from app.features.extraction.exceptions import AIExtractionError, InvalidLLMOutputError

_JSON_ARRAY_PATTERN = re.compile(r"\[.*\]", re.DOTALL)
_MARKDOWN_FENCE_PREFIXES = ("```json", "```")


def _strip_markdown_fences(text: str) -> str:
    """Some models wrap JSON in ```json ... ``` despite instructions not to."""
    stripped = text.strip()
    for prefix in _MARKDOWN_FENCE_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped.removeprefix(prefix)
            break
    return stripped.removesuffix("```").strip()


def _extract_json_array(raw_text: str) -> str:
    stripped = _strip_markdown_fences(raw_text)
    match = _JSON_ARRAY_PATTERN.search(stripped)
    return match.group(0) if match else stripped


def parse_json_array(raw_text: str) -> list[dict[str, Any]]:
    """Turn a provider's raw text response into a raw list of JSON objects.

    Provider-agnostic: operates only on the text every AIProvider returns, so
    it runs identically regardless of which provider produced it. Deliberately
    stops at "is this a JSON array" — cleaning, deduplication, defaults, and
    schema validation are the normalizer's job (`app.features.extraction.normalizer`),
    not the parser's.
    """
    json_text = _extract_json_array(raw_text)

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise AIExtractionError(AI_RESPONSE_NOT_JSON_MESSAGE) from exc

    if not isinstance(payload, list):
        raise InvalidLLMOutputError(AI_RESPONSE_NOT_ARRAY_MESSAGE)

    return payload
