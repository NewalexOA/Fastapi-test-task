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
    Creates database engine with proper configuration for pgbouncer.
    When using PgBouncer, we should:
    1. Use NullPool as connection pooling is handled by PgBouncer
    2. Disable prepared statements and statement cache
    3. Set proper isolation level
    """
    # Parse existing URL to add required parameters
    url = urlparse(settings.DATABASE_URL)
    query = parse_qs(url.query)
    
    # Add required parameters for pgbouncer compatibility
    query.update({
        "prepared_statement_cache_size": ["0"],
        "statement_cache_size": ["0"],
        "server_settings": ["{'statement_timeout': '60000'}", "{'idle_in_transaction_session_timeout': '60000'}"],
        "command_timeout": ["60"],
        "max_cached_statement_lifetime": ["0"],
        "max_cacheable_statement_size": ["0"]
    })
    
    # Reconstruct URL with new parameters
    new_url = urlunparse((
        url.scheme, url.netloc, url.path, url.params,
        urlencode(query, doseq=True), url.fragment
    ))
    
    return create_async_engine(
        new_url,
        poolclass=NullPool,  # Use NullPool with PgBouncer
        echo=settings.DB_ECHO,
        execution_options={
            "isolation_level": "READ COMMITTED"
        },
        connect_args={
            "server_settings": {
                "statement_timeout": "60000",
                "idle_in_transaction_session_timeout": "60000"
            },
            "command_timeout": 60
        }
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
