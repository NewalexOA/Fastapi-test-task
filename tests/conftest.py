import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from sqlalchemy.sql import text

# Глобальная настройка для всех асинхронных тестов
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@db:5432/postgres",
        isolation_level="AUTOCOMMIT"
    )
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def test_db(db_engine):
    """Create test database."""
    async with db_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS wallet_db_test"))
        await conn.execute(text("CREATE DATABASE wallet_db_test"))
        await conn.execute(text("""
            GRANT ALL PRIVILEGES ON DATABASE wallet_db_test TO wallet_user;
            ALTER DATABASE wallet_db_test OWNER TO wallet_user;
        """))
    
    test_engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@db:5432/wallet_db_test"
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    await test_engine.dispose()
    
    # Cleanup
    async with db_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS wallet_db_test"))

@pytest.fixture
async def session(test_db):
    """Create a test session."""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback() 