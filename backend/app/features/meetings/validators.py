"""Shared business-rule validators for meeting fields.

Plain functions (not a Pydantic mixin) so `MeetingCreate` and
`MeetingConfirmRequest` — which have different field optionality — can each
call the same rule without duplicating its logic or fighting BaseModel
multiple inheritance.
"""

from datetime import date, datetime, time

from app.core.constants.messages import (
    MEETING_DATE_IN_FUTURE_MESSAGE,
    MEETING_TIME_IN_FUTURE_MESSAGE,
)


def require_non_blank(value: str, message: str) -> str:
    """Trims whitespace and rejects a value that is empty (or all whitespace)."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(message)
    return trimmed


def validate_meeting_date_not_future(value: date | None) -> date | None:
    """Meeting notes can only be entered for meetings that already occurred."""
    if value is not None and value > date.today():
        raise ValueError(MEETING_DATE_IN_FUTURE_MESSAGE)
    return value


def validate_meeting_time_not_future(meeting_date: date | None, meeting_time: time | None) -> None:
    """If the (effective) meeting date is today, the time can't be in the future."""
    effective_date = meeting_date or date.today()
    if (
        effective_date == date.today()
        and meeting_time is not None
        and meeting_time > datetime.now().time()
    ):
        raise ValueError(MEETING_TIME_IN_FUTURE_MESSAGE)
