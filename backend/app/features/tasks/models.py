import uuid
from datetime import date as date_
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Uuid, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.constants.limits import MAX_OWNER_LENGTH
from app.core.enums import TaskPriority, TaskStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.features.meetings.models import Meeting


class Task(Base):
    """A single extracted, manageable task, always linked to its source meeting."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(MAX_OWNER_LENGTH), nullable=True, index=True)
    priority: Mapped[TaskPriority] = mapped_column(
        SqlEnum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SqlEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TaskStatus.TODO,
        index=True,
    )
    due_date: Mapped[date_ | None] = mapped_column(Date, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="tasks")
