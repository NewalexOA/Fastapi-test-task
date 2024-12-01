from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
import logging
import time
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=int(os.getenv('DB_POOL_SIZE', 50)),
    max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 25)),
    pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 60)),
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_use_lifo=True,
    execution_options={"isolation_level": "READ COMMITTED"}
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
