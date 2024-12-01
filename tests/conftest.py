import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
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
    # Connect directly to PostgreSQL (not through PgBouncer) to create database
    admin_engine = create_async_engine(
        "postgresql+asyncpg://wallet_user:wallet_password@db:5432/postgres",  # Прямое подключение к PostgreSQL
        isolation_level="AUTOCOMMIT",
        echo=True,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "max_cached_statement_lifetime": 0
        }
    )
    
    async with admin_engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(text(
            "SELECT 1 FROM pg_database WHERE datname = 'wallet_db_test'"
        ))
        exists = result.scalar()
        
        if exists:
            # Terminate existing connections
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = 'wallet_db_test'
                AND pid <> pg_backend_pid()
            """))
            # Drop existing database
            await conn.execute(text("DROP DATABASE IF EXISTS wallet_db_test"))
        
        # Create test database
        await conn.execute(text("CREATE DATABASE wallet_db_test"))
        # Grant privileges
        await conn.execute(text("""
            GRANT ALL PRIVILEGES ON DATABASE wallet_db_test TO wallet_user;
            ALTER DATABASE wallet_db_test OWNER TO wallet_user;
        """))
    
    await admin_engine.dispose()
    
    # Connect to test database to create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Create test index explicitly
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_wallets_balance ON wallets (balance);
        """))
    
    yield engine
    
    # Cleanup after tests
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