from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.constants.defaults import DEFAULT_MEETING_TITLE
from app.core.constants.messages import MEETING_NOT_FOUND_MESSAGE_TEMPLATE
from app.core.enums import ProcessingStatus
from app.core.exceptions import NotFoundError
from app.features.extraction.service import ExtractionService, get_extraction_service
from app.features.meetings.models import Meeting
from app.features.meetings.repository import MeetingRepository, get_meeting_repository
from app.features.meetings.schemas import (
    MeetingConfirmRequest,
    MeetingCreate,
    MeetingExtractionPreview,
)
from app.features.tasks.models import Task
from app.features.tasks.repository import TaskRepository, get_task_repository


class MeetingNotFoundError(NotFoundError):
    error_code = "meeting_not_found"


class MeetingService:
    """Human-in-the-loop extraction: preview (no persistence) -> user review
    on the client -> confirm (persistence, no AI call).

    `preview_extraction` and `save_reviewed_meeting` are deliberately two
    separate operations, not one pipeline — the whole point of the review
    step is that nothing reaches the database between them except what the
    user explicitly confirmed (see ARCHITECTURE.md §3, §15).
    """

    def __init__(
        self,
        meeting_repository: MeetingRepository,
        task_repository: TaskRepository,
        extraction_service: ExtractionService,
    ) -> None:
        self._meeting_repository = meeting_repository
        self._task_repository = task_repository
        self._extraction_service = extraction_service

    async def preview_extraction(self, payload: MeetingCreate) -> MeetingExtractionPreview:
        """Resolve defaults and run extraction. No DB writes at all."""
        meeting_date = payload.meeting_date or date.today()

        extracted = await self._extraction_service.extract(
            payload.raw_notes, reference_date=meeting_date
        )

        return MeetingExtractionPreview(
            title=payload.title or DEFAULT_MEETING_TITLE,
            meeting_date=meeting_date,
            meeting_time=payload.meeting_time or datetime.now().time(),
            raw_notes=payload.raw_notes,
            tasks=extracted,
        )

    async def save_reviewed_meeting(self, payload: MeetingConfirmRequest) -> Meeting:
        """Persist exactly what the user reviewed and confirmed. No AI call."""
        meeting = Meeting(
            title=payload.title,
            meeting_date=payload.meeting_date,
            meeting_time=payload.meeting_time,
            raw_notes=payload.raw_notes,
            processing_status=ProcessingStatus.COMPLETED,
        )
        meeting = await self._meeting_repository.create(meeting)

        tasks = [
            Task(
                meeting_id=meeting.id,
                description=dto.description,
                owner=dto.owner,
                priority=dto.priority,
                due_date=dto.due_date,
                source_text=dto.source_text,
            )
            for dto in payload.tasks
        ]
        if tasks:
            await self._task_repository.bulk_create(tasks)

        return await self.get_meeting_with_tasks(meeting.id)

    async def get_meeting_with_tasks(self, meeting_id: UUID) -> Meeting:
        meeting = await self._meeting_repository.get_with_tasks(meeting_id)
        if meeting is None:
            raise MeetingNotFoundError(
                MEETING_NOT_FOUND_MESSAGE_TEMPLATE.format(meeting_id=meeting_id)
            )
        return meeting


def get_meeting_service(
    meeting_repository: Annotated[MeetingRepository, Depends(get_meeting_repository)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    extraction_service: Annotated[ExtractionService, Depends(get_extraction_service)],
) -> MeetingService:
    return MeetingService(meeting_repository, task_repository, extraction_service)
