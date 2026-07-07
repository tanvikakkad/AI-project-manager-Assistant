import uuid
from datetime import date as date_
from datetime import datetime
from datetime import time as time_
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, String, Text, Time, Uuid, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.constants.defaults import DEFAULT_MEETING_TITLE
from app.core.constants.limits import MAX_TITLE_LENGTH
from app.core.enums import ProcessingStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.features.tasks.models import Task


class Meeting(Base):
    """A single pasted meeting-notes submission and its extraction lifecycle.

    `title`/`meeting_date`/`meeting_time` are optional on input; the defaults
    below are a defensive fallback only — the actual "apply a sensible
    default when omitted" decision is made by MeetingService (Phase 5).
    """

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(
        String(MAX_TITLE_LENGTH), nullable=False, default=DEFAULT_MEETING_TITLE
    )
    meeting_date: Mapped[date_] = mapped_column(
        Date, nullable=False, default=date_.today, index=True
    )
    meeting_time: Mapped[time_] = mapped_column(
        Time, nullable=False, default=lambda: datetime.now().time()
    )
    raw_notes: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SqlEnum(
            ProcessingStatus,
            name="processing_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ProcessingStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
