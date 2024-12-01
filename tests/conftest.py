import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from sqlalchemy.sql import text

# Глобальная настройка для всех асинхронных тестов
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@db:5432/postgres",
        isolation_level="AUTOCOMMIT"
    )
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture(scope="session")
async def test_db(db_engine):
    """Create test database."""
    engine = await anext(db_engine)  # Получаем engine из генератора
    async with engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS wallet_db_test"))
        await conn.execute(text("CREATE DATABASE wallet_db_test"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON DATABASE wallet_db_test TO wallet_user"))
        await conn.execute(text("ALTER DATABASE wallet_db_test OWNER TO wallet_user"))
    
    test_engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@db:5432/wallet_db_test",
        isolation_level="SERIALIZABLE"
    )
    
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wallets_balance ON wallets (balance)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wallets_balance_ops ON wallets USING btree (id, balance)"))
        yield test_engine
    finally:
        await test_engine.dispose()
        async with engine.connect() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS wallet_db_test"))

@pytest.fixture(autouse=True)
async def setup_test_db(test_db):
    """Setup test database before each test."""
    async with test_db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_db.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def session(test_db):
    """Create a test session."""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio_mode("strict")
def pytest_configure(config):
    """Configure pytest-asyncio mode."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    ) 