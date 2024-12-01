"""
Database configuration module for the wallet service.
Handles database connection settings, session management, and connection pooling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
import logging
import time
import os
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class Settings(BaseSettings):
    """
    Database configuration settings.
    Loads settings from environment variables or .env file.
    
    Attributes:
        DATABASE_URL (str): Database connection URL
        DB_ECHO (bool): Enable SQLAlchemy query logging
    """
    DATABASE_URL: str = "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/wallet_db"
    DB_ECHO: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()

def get_engine():
    """
    Creates SQLAlchemy engine with proper configuration for PgBouncer
    """
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "statement_timeout": 60000,
            "idle_in_transaction_session_timeout": 60000
        }
    }
    
    return create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,  # Используем NullPool с PgBouncer
        echo=settings.DB_ECHO,
        connect_args=connect_args,
        execution_options={"isolation_level": "READ COMMITTED"}
    )

async_session = async_sessionmaker(
    get_engine(),
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates and yields a database session.
    Ensures proper cleanup of the session after use.
    
    Yields:
        AsyncSession: Database session for executing queries
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def monitored_session():
    """
    Context manager that monitors database session duration.
    Logs warning if transaction takes longer than 1 second.
    
    Yields:
        AsyncSession: Monitored database session
    
    Example:
        async with monitored_session() as session:
            await session.execute(query)
    """
    start_time = time.monotonic()
    session = async_session()
    try:
        yield session
        duration = time.monotonic() - start_time
        if duration > 1.0:
            logging.warning(f"Long database transaction detected: {duration:.2f}s")
    finally:
        await session.close()
