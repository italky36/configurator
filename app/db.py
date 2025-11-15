"""Database engine, session, and helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Declarative base class for all models."""


def _create_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, echo=False, future=True)


engine: AsyncEngine = _create_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for database sessions."""

    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create database tables."""

    from . import models  # noqa: F401  Ensure models imported for metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
