import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/wallet_db_test"

@pytest.fixture(scope="session")
@pytest.mark.asyncio(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        pool_size=5,
        max_overflow=5
    )
    return engine

@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def session(engine, create_tables):
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback() 