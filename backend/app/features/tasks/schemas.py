from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants.limits import MAX_DESCRIPTION_LENGTH, MAX_OWNER_LENGTH
from app.core.enums import TaskPriority, TaskStatus


class TaskRead(BaseModel):
    """API representation of a Task row."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meeting_id: UUID
    description: str
    owner: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: date | None
    source_text: str | None
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    """Partial update payload. Only fields present in the request are applied —
    TaskService reads this via `model_dump(exclude_unset=True)`."""

    description: str | None = Field(default=None, min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    owner: str | None = Field(default=None, max_length=MAX_OWNER_LENGTH)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: date | None = None


class TaskFilterParams(BaseModel):
    """Structured list/filter query params — additive if pagination is added later."""

    owner: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
