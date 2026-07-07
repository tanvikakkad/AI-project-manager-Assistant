from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TaskPriority, TaskStatus
from app.db.repository import BaseRepository
from app.db.session import get_db
from app.features.tasks.models import Task


class TaskRepository(BaseRepository[Task]):
    """All SQL for the `tasks` table. No business rules live here.

    `find_all`'s filter combination and `update`'s field selection are
    decided by TaskService (Phase 5); this class only translates already-made
    decisions into SQLAlchemy statements.
    """

    model = Task

    async def find_all(
        self,
        *,
        owner: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> Sequence[Task]:
        stmt = select(Task)
        if owner is not None:
            stmt = stmt.where(Task.owner == owner)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        stmt = stmt.order_by(Task.created_at.desc())

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def bulk_create(self, tasks: Sequence[Task]) -> Sequence[Task]:
        self._session.add_all(tasks)
        await self._session.commit()
        for task in tasks:
            await self._session.refresh(task)
        return tasks

    async def update(self, task: Task, fields: dict[str, Any]) -> Task:
        for field, value in fields.items():
            setattr(task, field, value)
        await self._session.commit()
        await self._session.refresh(task)
        return task


def get_task_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> TaskRepository:
    return TaskRepository(session)
