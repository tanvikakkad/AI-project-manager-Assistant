from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from fastapi import status as http_status

from app.core.constants.api import API_V1_PREFIX
from app.core.enums import TaskPriority, TaskStatus
from app.core.responses import APIResponse, success_response
from app.features.tasks.schemas import TaskFilterParams, TaskRead, TaskUpdate
from app.features.tasks.service import TaskService, get_task_service

router = APIRouter(prefix=f"{API_V1_PREFIX}/tasks", tags=["tasks"])

_CSV_MEDIA_TYPE = "text/csv"
_CSV_FILENAME = "tasks.csv"


def get_task_filter_params(
    owner: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> TaskFilterParams:
    """Groups the list endpoint's query params into one structured object."""
    return TaskFilterParams(owner=owner, status=status, priority=priority)


@router.get("", response_model=APIResponse[list[TaskRead]])
async def list_tasks(
    filters: Annotated[TaskFilterParams, Depends(get_task_filter_params)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> APIResponse[list[TaskRead]]:
    tasks = await service.list_tasks(
        owner=filters.owner, status=filters.status, priority=filters.priority
    )
    return success_response([TaskRead.model_validate(task) for task in tasks])


@router.get("/export/csv")
async def export_tasks_csv(
    filters: Annotated[TaskFilterParams, Depends(get_task_filter_params)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Response:
    csv_content = await service.export_csv(
        owner=filters.owner, status=filters.status, priority=filters.priority
    )
    return Response(
        content=csv_content,
        media_type=_CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{_CSV_FILENAME}"'},
    )


@router.get("/{task_id}", response_model=APIResponse[TaskRead])
async def get_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> APIResponse[TaskRead]:
    task = await service.get_task(task_id)
    return success_response(TaskRead.model_validate(task))


@router.patch("/{task_id}", response_model=APIResponse[TaskRead])
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> APIResponse[TaskRead]:
    task = await service.update_task(task_id, payload)
    return success_response(TaskRead.model_validate(task))


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    await service.delete_task(task_id)
