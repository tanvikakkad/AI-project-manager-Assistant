import csv
import io
from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.core.constants.messages import TASK_NOT_FOUND_MESSAGE_TEMPLATE
from app.core.enums import TaskPriority, TaskStatus
from app.core.exceptions import NotFoundError
from app.features.tasks.models import Task
from app.features.tasks.repository import TaskRepository, get_task_repository
from app.features.tasks.schemas import TaskUpdate

_CSV_HEADER = (
    "id",
    "description",
    "owner",
    "priority",
    "status",
    "due_date",
    "meeting_id",
    "created_at",
    "updated_at",
)


class TaskNotFoundError(NotFoundError):
    error_code = "task_not_found"


class TaskService:
    """Business rules for tasks: filtering, update semantics. No SQL, no HTTP."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def list_tasks(
        self,
        *,
        owner: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> Sequence[Task]:
        return await self._repository.find_all(owner=owner, status=status, priority=priority)

    async def get_task(self, task_id: UUID) -> Task:
        task = await self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(TASK_NOT_FOUND_MESSAGE_TEMPLATE.format(task_id=task_id))
        return task

    async def update_task(self, task_id: UUID, payload: TaskUpdate) -> Task:
        task = await self.get_task(task_id)
        fields: dict[str, Any] = payload.model_dump(exclude_unset=True)
        if not fields:
            return task
        return await self._repository.update(task, fields)

    async def delete_task(self, task_id: UUID) -> None:
        task = await self.get_task(task_id)
        await self._repository.delete(task)

    async def export_csv(
        self,
        *,
        owner: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> str:
        """Builds CSV text for the same filter combination as `list_tasks`."""
        tasks = await self.list_tasks(owner=owner, status=status, priority=priority)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_CSV_HEADER)
        for task in tasks:
            writer.writerow(
                (
                    str(task.id),
                    task.description,
                    task.owner or "",
                    task.priority.value,
                    task.status.value,
                    task.due_date.isoformat() if task.due_date else "",
                    str(task.meeting_id),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                )
            )
        return buffer.getvalue()


def get_task_service(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository)
