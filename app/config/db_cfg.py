from sqlalchemy import create_engine
from typing import AsyncGenerator, Generator
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.main_cfg import settings

"""
Модуль конфигурации сессии базы данных.
Предоставляет функционал для создания и управления сессиями PostgreSQL.
"""

# --- Формирование URL ---
SYNC_DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# --- Синхронный движок (для Alembic / create_all sync-утилит) ---
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=bool(settings.DEBUG_MODE),
    future=True,
)

# Синхронная фабрика сессий (если где-то нужна синхронная сессия)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# --- Асинхронный движок и фабрика сессий ---
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=bool(settings.DEBUG_MODE),
    future=True,
)

async_session = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# --- Зависимости для FastAPI ---
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная зависимость для FastAPI.
    Usage:
        async def endpoint(session: AsyncSession = Depends(get_async_session))
    """
    async with async_session() as session:
        yield session


def get_db() -> Generator:
    """
    Генератор для создания и управления сессией базы данных.

    Yields:
        SessionLocal: Объект сессии базы данных PostgreSQL

    Note:
        Автоматически закрывает сессию после использования
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()