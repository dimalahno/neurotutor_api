from typing import Type, TypeVar, Generic, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, obj_id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await session.scalar(stmt)
        return result

    async def get_all(self, session: AsyncSession) -> List[ModelType]:
        stmt = select(self.model)
        result = await session.scalars(stmt)
        return list(result)

    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        obj = self.model(**data)
        session.add(obj)
        await session.flush()
        return obj

    async def update(self, session: AsyncSession, obj: ModelType, data: dict) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)
        await session.flush()
        return obj

    async def delete(self, session: AsyncSession, obj: ModelType) -> None:
        await session.delete(obj)
        await session.flush()
