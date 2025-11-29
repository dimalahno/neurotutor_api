from typing import AsyncGenerator

from app.config.db_cfg import async_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repositories import (
    UserRepository,
    RoleDictionaryRepository,
    StatusDictionaryRepository,
    UserTokenRepository,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def get_user_repo() -> UserRepository:
    return UserRepository()


def get_role_repo() -> RoleDictionaryRepository:
    return RoleDictionaryRepository()


def get_status_repo() -> StatusDictionaryRepository:
    return StatusDictionaryRepository()


def get_token_repo() -> UserTokenRepository:
    return UserTokenRepository()
