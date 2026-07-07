from datetime import date, datetime, time
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants.limits import MAX_RAW_NOTES_LENGTH, MAX_TITLE_LENGTH
from app.core.constants.messages import MEETING_NOTES_REQUIRED_MESSAGE
from app.core.enums import ProcessingStatus
from app.features.extraction.schemas import ExtractedTaskDTO
from app.features.meetings.validators import (
    require_non_blank,
    validate_meeting_date_not_future,
    validate_meeting_time_not_future,
)
from app.features.tasks.schemas import TaskRead


class MeetingCreate(BaseModel):
    """Request payload for extracting tasks from pasted notes.

    Title/date/time are optional and user-provided only — the LLM never
    infers meeting metadata, only tasks (see ARCHITECTURE.md §29).
    """

    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    meeting_date: date | None = None
    meeting_time: time | None = None
    raw_notes: str = Field(min_length=1, max_length=MAX_RAW_NOTES_LENGTH)

    @field_validator("title")
    @classmethod
    def _trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("raw_notes")
    @classmethod
    def _trim_and_require_notes(cls, value: str) -> str:
        return require_non_blank(value, MEETING_NOTES_REQUIRED_MESSAGE)

    @field_validator("meeting_date")
    @classmethod
    def _validate_meeting_date(cls, value: date | None) -> date | None:
        return validate_meeting_date_not_future(value)

    @model_validator(mode="after")
    def _validate_meeting_time(self) -> Self:
        validate_meeting_time_not_future(self.meeting_date, self.meeting_time)
        return self


class MeetingExtractionPreview(BaseModel):
    """Response of the extract-only step: nothing is persisted yet.

    Echoes back the resolved meeting metadata (defaults already applied) so
    the client can round-trip it unchanged into `MeetingConfirmRequest` once
    the user has reviewed/edited the proposed tasks.
    """

    title: str
    meeting_date: date
    meeting_time: time
    raw_notes: str
    tasks: list[ExtractedTaskDTO]


class MeetingConfirmRequest(BaseModel):
    """Request payload for the confirm step: the human-reviewed task list to persist.

    Reuses `ExtractedTaskDTO` for `tasks` — the shape of "a task pending
    review" and "a task ready to persist" is identical, so there is no
    separate, duplicate schema for it. Re-validates the same business rules
    as `MeetingCreate` — the client echoes these fields back unchanged, but
    the backend never trusts a client-supplied value without re-checking it.
    """

    title: str = Field(max_length=MAX_TITLE_LENGTH)
    meeting_date: date
    meeting_time: time
    raw_notes: str = Field(min_length=1, max_length=MAX_RAW_NOTES_LENGTH)
    tasks: list[ExtractedTaskDTO]

    @field_validator("raw_notes")
    @classmethod
    def _trim_and_require_notes(cls, value: str) -> str:
        return require_non_blank(value, MEETING_NOTES_REQUIRED_MESSAGE)

    @field_validator("meeting_date")
    @classmethod
    def _validate_meeting_date(cls, value: date) -> date:
        return validate_meeting_date_not_future(value)

    @model_validator(mode="after")
    def _validate_meeting_time(self) -> Self:
        validate_meeting_time_not_future(self.meeting_date, self.meeting_time)
        return self


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    meeting_date: date
    meeting_time: time
    raw_notes: str
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime


class MeetingWithTasksRead(MeetingRead):
    """Returned after confirmation: the meeting plus every task saved for it."""

    tasks: list[TaskRead]
