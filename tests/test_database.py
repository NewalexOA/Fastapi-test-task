import pytest
from app.database import get_session, monitored_session, get_engine
from unittest.mock import patch
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine

# Глобальная настройка для всех тестов в файле
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_session_lifecycle():
    """Test session creation and cleanup"""
    async for session in get_session():
        assert session is not None
        assert session.is_active
        break

@pytest.mark.asyncio
async def test_long_transaction_monitoring():
    """Test monitoring of long-running transactions"""
    with patch("time.monotonic") as mock_time:
        mock_time.side_effect = [0, 2.0]  # Simulate 2 second transaction
        async with monitored_session():
            # Do some long operation
            pass
        # Check that warning was logged

@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_test_db")
async def test_database_indexes(test_db):
    """Test that required indexes exist"""
    engine = await anext(test_db)  # Получаем engine из генератора
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'wallets'
        """))
        indexes = [row[0] for row in result.fetchall()]
        assert "idx_wallets_balance" in indexes
        assert "idx_wallets_balance_ops" in indexes  # Проверяем также индекс из changeSet 002

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test handling of concurrent operations"""
    async for session in get_session():
        # Create test wallet
        wallet_id = str(uuid4())
        result = await session.execute(
            text("INSERT INTO wallets (id, balance) VALUES (:id, :balance) RETURNING id"),
            {"id": wallet_id, "balance": 100}
        )
        await session.commit()
        
        # Simulate concurrent operations
        async def update_balance():
            async for inner_session in get_session():
                try:
                    await inner_session.execute(
                        text("""
                            UPDATE wallets 
                            SET balance = balance + :amount 
                            WHERE id = :id
                            AND balance >= :amount
                        """),
                        {"id": wallet_id, "amount": -10}
                    )
                    await inner_session.commit()
                except OperationalError:
                    await inner_session.rollback()
                    return False
                return True

        # Run concurrent updates
        results = await asyncio.gather(*[update_balance() for _ in range(5)])
        
        # Verify final balance
        result = await session.execute(
            text("SELECT balance FROM wallets WHERE id = :id"),
            {"id": wallet_id}
        )
        final_balance = result.scalar()
        
        # Only successful operations should have modified the balance
        successful_ops = len([r for r in results if r])
        assert final_balance == 100 - (successful_ops * 10)

@pytest.mark.asyncio
async def test_database_connection():
    """Test that database connection works with PgBouncer"""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row[0] == 1

@pytest.mark.asyncio
async def test_pgbouncer_connection():
    """Test that connection works properly with PgBouncer"""
    engine = get_engine()
    async with engine.connect() as conn:
        # Test basic query
        result = await conn.execute(text("SELECT 1"))
        value = result.scalar_one()
        assert value == 1
        
        # Test transaction in separate connection
        async with engine.begin() as trans_conn:
            result = await trans_conn.execute(text("SELECT 1"))
            value = result.scalar_one()
            assert value == 1
