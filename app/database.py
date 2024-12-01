"""
Database configuration module for the wallet service.
Handles database connection settings, session management, and connection pooling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
import logging
import time
import os
from sqlalchemy.pool import AsyncAdaptedQueuePool
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class Settings(BaseSettings):
    """
    Database configuration settings.
    Loads settings from environment variables or .env file.
    
    Attributes:
        DATABASE_URL (str): Database connection URL
        DB_POOL_SIZE (int): Maximum number of database connections in the pool
        DB_MAX_OVERFLOW (int): Maximum number of connections that can be created beyond pool_size
        DB_POOL_TIMEOUT (int): Number of seconds to wait before timing out on getting a connection
        DB_ECHO (bool): Enable SQLAlchemy query logging
    """
    DATABASE_URL: str = "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/wallet_db"
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 20
    DB_ECHO: bool = False

    def get_database_url_with_params(self) -> str:
        """
        Adds application_name parameter to database URL for connection tracking.
        
        Returns:
            str: Modified database URL with application_name parameter
        """
        url = urlparse(self.DATABASE_URL)
        query_params = parse_qs(url.query)
        query_params['application_name'] = ['wallet_service']
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(
            (url.scheme, url.netloc, url.path, url.params, new_query, url.fragment)
        )

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()
engine = create_async_engine(
    settings.get_database_url_with_params(),
    echo=settings.DB_ECHO,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_use_lifo=True,
    execution_options={"isolation_level": "READ COMMITTED"},
    connect_args={"command_timeout": 10}
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
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
