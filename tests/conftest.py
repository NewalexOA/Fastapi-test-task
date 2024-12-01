import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from sqlalchemy.pool import NullPool
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.sql import text

TEST_DATABASE_URL = "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/wallet_db_test"

@pytest.fixture(scope="session")
@pytest.mark.asyncio(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    """Create test database engine with proper settings"""
    return create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "max_cached_statement_lifetime": 0
        }
    )

@pytest.fixture(scope="session")
async def create_tables(engine):
    """Create test database and tables"""
    # Подключаемся к базе postgres для создания тестовой БД
    admin_engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/postgres",
        isolation_level="AUTOCOMMIT",
        echo=True,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "max_cached_statement_lifetime": 0
        }
    )
    
    async with admin_engine.connect() as conn:
        # Проверяем существование БД
        result = await conn.execute(text(
            "SELECT 1 FROM pg_database WHERE datname = 'wallet_db_test'"
        ))
        exists = result.scalar()
        
        if not exists:
            # Закрываем все подключения к БД перед удалением
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = 'wallet_db_test'
            """))
            # Создаем тестовую БД
            await conn.execute(text("CREATE DATABASE wallet_db_test"))
            # Даем права на тестовую БД
            await conn.execute(text(f"""
                GRANT ALL PRIVILEGES ON DATABASE wallet_db_test TO wallet_user;
                ALTER DATABASE wallet_db_test OWNER TO wallet_user;
            """))
    
    await admin_engine.dispose()
    
    # Подключаемся к тестовой БД для создания таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Создаем индекс для тестирования
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_wallets_balance ON wallets (balance);
        """))
    
    yield engine
    
    # Очистка после тестов
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