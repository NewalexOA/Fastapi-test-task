import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from sqlalchemy.pool import NullPool
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TEST_DATABASE_URL = "postgresql+asyncpg://wallet_user:wallet_password@pgbouncer:6432/wallet_db_test"

@pytest.fixture(scope="session")
@pytest.mark.asyncio(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    # Parse existing URL to add required parameters
    url = urlparse(TEST_DATABASE_URL)
    query = parse_qs(url.query)
    
    # Add required parameters for pgbouncer compatibility
    query.update({
        "prepared_statement_cache_size": ["0"],
        "statement_cache_size": ["0"],
        "server_settings": ["{'statement_timeout': '60000'}", "{'idle_in_transaction_session_timeout': '60000'}"]
    })
    
    # Reconstruct URL with new parameters
    new_url = urlunparse((
        url.scheme, url.netloc, url.path, url.params,
        urlencode(query, doseq=True), url.fragment
    ))
    
    return create_async_engine(
        new_url,
        poolclass=NullPool,
        echo=True,
        execution_options={
            "isolation_level": "READ COMMITTED"
        }
    )

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