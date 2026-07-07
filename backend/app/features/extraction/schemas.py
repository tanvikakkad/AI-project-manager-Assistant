from datetime import date

from pydantic import BaseModel, Field

from app.core.constants.limits import MAX_DESCRIPTION_LENGTH, MAX_OWNER_LENGTH
from app.core.enums import TaskPriority


class ExtractedTaskDTO(BaseModel):
    """Validated shape of a single task as returned by any AIProvider.

    This is the one place the LLM's output is trusted from — every field the
    model claims to have extracted is checked here (types, lengths, enum
    membership) before it can reach the database.
    """

    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    owner: str | None = Field(default=None, max_length=MAX_OWNER_LENGTH)
    due_date: date | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    source_text: str | None = None
