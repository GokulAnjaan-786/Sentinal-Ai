"""
Database Configuration Module
==============================

This module configures the SQLAlchemy async database engine, session factory,
and base model class for the SentinelAI platform.

Key Components:
    - create_async_engine: Async engine for high-performance database operations
    - async_session_factory: Session factory for creating database sessions
    - Base: SQLAlchemy declarative base class for all ORM models
    - get_db_session: FastAPI dependency for database session injection

The async engine is used throughout the application to ensure non-blocking
database operations, which is critical for handling concurrent requests
in a real-time threat detection system.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

"""
Naming convention for database constraints.
This ensures consistent naming of indexes, foreign keys, and other constraints
across the application, making database migrations and debugging easier.
"""
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in SentinelAI.

    All database models must inherit from this class. It provides:
    - Consistent metadata configuration with naming conventions
    - Common utility methods (to_dict, __repr__)
    - Standardized primary key generation (UUID-based)

    Example:
        class User(Base):
            __tablename__ = "users"
            id = Column(UUID, primary_key=True, default=uuid4)
            username = Column(String(100), nullable=False)
    """
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def to_dict(self) -> dict:
        """
        Serialize the model instance to a dictionary.

        Iterates over all column attributes and creates a dictionary
        mapping column names to their values. Handles UUID serialization
        and datetime conversion automatically.

        Returns:
            dict: Dictionary representation of the model instance.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value is not None:
                # Handle UUID serialization
                if hasattr(value, '__str__'):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
            else:
                result[column.name] = None
        return result


"""
Async database engine instance.
This engine handles connection pooling and async communication with PostgreSQL.
The engine is created once and shared across the application.
"""
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before use to handle dropped connections
    echo=settings.APP_DEBUG,  # Log SQL statements in debug mode
)

"""
Async session factory.
Each request gets its own session from this factory. Sessions are scoped
to individual requests and automatically closed when the request completes.
"""
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep attribute access after commit
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    This generator function yields a database session and ensures it is
    properly closed after the request is processed. It follows the
    dependency injection pattern used throughout the FastAPI application.

    Yields:
        AsyncSession: An async database session instance.

    Usage in route handlers:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI routes.

    This is used in background tasks, services, and ML pipelines where
    FastAPI dependency injection is not available.

    Usage:
        async with get_db_session_context() as session:
            result = await session.execute(select(User))
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session context error: {str(e)}")
            raise
        finally:
            await session.close()
