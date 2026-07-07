from typing import ClassVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelType: Base]:
    """Generic async CRUD shared by every feature repository.

    Feature repositories subclass this for identical get-by-id/delete
    behavior and add their own entity-specific query methods (dynamic
    filters, bulk-create, status transitions). Each mutating method commits
    its own unit of work — there is no request-wide auto-commit — because
    the meeting/task extraction flow needs the meeting row durably persisted
    independently of, and before, the AI call (see ARCHITECTURE.md, §3).
    """

    model: ClassVar[type[Base]]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        return await self._session.get(self.model, entity_id)

    async def delete(self, entity: ModelType) -> None:
        await self._session.delete(entity)
        await self._session.commit()
