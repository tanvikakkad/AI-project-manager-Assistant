from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.core.constants.api import API_V1_PREFIX
from app.core.responses import APIResponse, success_response
from app.features.meetings.schemas import (
    MeetingConfirmRequest,
    MeetingCreate,
    MeetingExtractionPreview,
    MeetingWithTasksRead,
)
from app.features.meetings.service import MeetingService, get_meeting_service

router = APIRouter(prefix=f"{API_V1_PREFIX}/meetings", tags=["meetings"])


@router.post("/extract", response_model=APIResponse[MeetingExtractionPreview])
async def extract_meeting_preview(
    payload: MeetingCreate,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> APIResponse[MeetingExtractionPreview]:
    """Runs AI extraction only. Nothing is persisted — the client reviews
    the returned tasks and calls `POST /meetings` to save them."""
    preview = await service.preview_extraction(payload)
    return success_response(preview)


@router.post(
    "",
    response_model=APIResponse[MeetingWithTasksRead],
    status_code=http_status.HTTP_201_CREATED,
)
async def confirm_meeting(
    payload: MeetingConfirmRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> APIResponse[MeetingWithTasksRead]:
    """Persists the meeting and exactly the (possibly edited) tasks the user
    confirmed. No AI call happens here."""
    meeting = await service.save_reviewed_meeting(payload)
    return success_response(MeetingWithTasksRead.model_validate(meeting))


@router.get("/{meeting_id}", response_model=APIResponse[MeetingWithTasksRead])
async def get_meeting(
    meeting_id: UUID,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> APIResponse[MeetingWithTasksRead]:
    meeting = await service.get_meeting_with_tasks(meeting_id)
    return success_response(MeetingWithTasksRead.model_validate(meeting))
