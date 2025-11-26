from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.models.user_models import (
    User,
    DUserRole,
    DUserStatus,
    UserRole,
    UserToken,
)
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str):
        stmt = select(User).where(User.email == email)
        return await session.scalar(stmt)


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self):
        super().__init__(UserRole)


class UserTokenRepository(BaseRepository[UserToken]):
    def __init__(self):
        super().__init__(UserToken)

    async def get_active_tokens(self, session: AsyncSession, user_id: int):
        stmt = (
            select(UserToken)
            .where(UserToken.user_id == user_id)
            .where(UserToken.revoked_at.is_(None))
        )
        result = await session.scalars(stmt)
        return list(result)


class RoleDictionaryRepository(BaseRepository[DUserRole]):
    def __init__(self):
        super().__init__(DUserRole)

    async def get_by_code(self, session: AsyncSession, code: str):
        stmt = select(DUserRole).where(DUserRole.code == code)
        return await session.scalar(stmt)


class StatusDictionaryRepository(BaseRepository[DUserStatus]):
    def __init__(self):
        super().__init__(DUserStatus)

    async def get_by_code(self, session: AsyncSession, code: str):
        stmt = select(DUserStatus).where(DUserStatus.code == code)
        return await session.scalar(stmt)
