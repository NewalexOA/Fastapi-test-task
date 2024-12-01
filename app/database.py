from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
import logging
import time
import os
from sqlalchemy.pool import AsyncAdaptedQueuePool

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 20
    DB_ECHO: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()
engine = create_async_engine(
    settings.DATABASE_URL,
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
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def monitored_session():
    start_time = time.monotonic()
    session = async_session()
    try:
        yield session
        duration = time.monotonic() - start_time
        if duration > 1.0:
            logging.warning(f"Long database transaction detected: {duration:.2f}s")
    finally:
        await session.close()
