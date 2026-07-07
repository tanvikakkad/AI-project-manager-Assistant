from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ProcessingStatus
from app.db.repository import BaseRepository
from app.db.session import get_db
from app.features.meetings.models import Meeting


class MeetingRepository(BaseRepository[Meeting]):
    """All SQL for the `meetings` table. No business rules live here."""

    model = Meeting

    async def create(self, meeting: Meeting) -> Meeting:
        self._session.add(meeting)
        await self._session.commit()
        await self._session.refresh(meeting)
        return meeting

    async def update_status(self, meeting: Meeting, status: ProcessingStatus) -> Meeting:
        meeting.processing_status = status
        await self._session.commit()
        await self._session.refresh(meeting)
        return meeting

    async def get_with_tasks(self, meeting_id: UUID) -> Meeting | None:
        # `populate_existing` is required here: `Meeting.tasks` is `lazy="selectin"`,
        # so if this `Meeting` is already in the session's identity map with an
        # (empty, stale) `.tasks` already loaded — e.g. right after `create()`,
        # before any tasks existed — `selectinload` alone will NOT refresh it,
        # since SQLAlchemy skips already-loaded relationships by default.
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(selectinload(Meeting.tasks))
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


def get_meeting_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> MeetingRepository:
    return MeetingRepository(session)
