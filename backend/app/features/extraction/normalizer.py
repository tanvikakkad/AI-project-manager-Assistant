from datetime import datetime
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.core.constants.messages import AI_RESPONSE_INVALID_TASK_MESSAGE
from app.core.enums import TaskPriority
from app.features.extraction.exceptions import InvalidLLMOutputError
from app.features.extraction.schemas import ExtractedTaskDTO

# Date formats tolerated from providers that don't strictly follow the
# prompt's requested "YYYY-MM-DD" — tried in order, first match wins.
_DATE_INPUT_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y")


def _clean_text(value: str) -> str:
    """Trim and collapse any run of whitespace (spaces, tabs, newlines) to one space."""
    return " ".join(value.split())


def _normalize_owner(owner: Any) -> Any:
    if not isinstance(owner, str):
        return owner
    cleaned = _clean_text(owner)
    return cleaned.title() if cleaned else None


def _normalize_optional_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = _clean_text(value)
    return cleaned or None


def _normalize_due_date(value: Any) -> Any:
    """Best-effort: fold any recognized date string into a single ISO format."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return None
    for date_format in _DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            continue
    return text  # unrecognized format — let DTO validation reject it explicitly


def _normalize_priority(value: Any) -> Any:
    """Missing/empty priority defaults to MEDIUM; anything else is left as-is
    so DTO validation can reject genuinely invalid values."""
    if value is None or value == "":
        return TaskPriority.MEDIUM.value
    return value


def _dedup_key(item: dict[str, Any]) -> tuple[str, str, str]:
    description = str(item.get("description") or "").strip().lower()
    owner = str(item.get("owner") or "").strip().lower()
    due_date = str(item.get("due_date") or "")
    return (description, owner, due_date)


def _clean_item(raw_item: dict[str, Any]) -> dict[str, Any]:
    item = dict(raw_item)
    if isinstance(item.get("description"), str):
        # Description is required (non-nullable): clean it, but never coerce
        # to None — an empty result must still fail DTO validation explicitly.
        item["description"] = _clean_text(item["description"])
    if "owner" in item:
        item["owner"] = _normalize_owner(item["owner"])
    if "source_text" in item:
        item["source_text"] = _normalize_optional_text(item["source_text"])
    if "due_date" in item:
        item["due_date"] = _normalize_due_date(item["due_date"])
    item["priority"] = _normalize_priority(item.get("priority"))
    return item


def normalize(raw_items: list[dict[str, Any]]) -> list[ExtractedTaskDTO]:
    """Clean, deduplicate, default, and validate raw parsed JSON items into DTOs.

    The single point where the business layer's guarantee of "clean,
    deterministic data regardless of provider output" is enforced —
    completely independent of FastAPI, SQLAlchemy, and any specific LLM SDK.
    Responsibilities: whitespace/formatting normalization, value trimming,
    duplicate removal (same description + owner + due_date), consistent
    owner-name casing, single-ISO-format dates, and sensible defaults.
    """
    seen_keys: set[tuple[str, str, str]] = set()
    cleaned_items: list[dict[str, Any]] = []

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        item = _clean_item(raw_item)
        key = _dedup_key(item)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        cleaned_items.append(item)

    try:
        return [ExtractedTaskDTO.model_validate(item) for item in cleaned_items]
    except PydanticValidationError as exc:
        # include_context=False: avoids a non-JSON-serializable exception
        # instance ending up in ctx.error for any custom-validator failures.
        raise InvalidLLMOutputError(
            AI_RESPONSE_INVALID_TASK_MESSAGE,
            details={"errors": exc.errors(include_context=False)},
        ) from exc
