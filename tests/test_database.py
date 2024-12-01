import pytest
from app.database import get_session, monitored_session, get_engine
from unittest.mock import patch
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
import asyncio

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
async def test_database_indexes(engine):
    """Test that required indexes exist"""
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'wallets'
        """))
        indexes = [row[0] for row in result]
        assert "idx_wallets_balance" in indexes

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test handling of concurrent operations"""
    async for session in get_session():
        # Create test wallet
        result = await session.execute(
            text("INSERT INTO wallets (id, balance) VALUES (:id, :balance) RETURNING id"),
            {"id": "test-wallet", "balance": 100}
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
                        {"id": "test-wallet", "amount": -10}
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
            {"id": "test-wallet"}
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
        assert await result.scalar() == 1

@pytest.mark.asyncio
async def test_pgbouncer_connection():
    """Test that connection works properly with PgBouncer"""
    engine = get_engine()
    async with engine.connect() as conn:
        # Test basic query
        result = await conn.execute(text("SELECT 1"))
        assert await result.scalar() == 1
        
        # Test transaction
        async with conn.begin():
            result = await conn.execute(text("SELECT 1"))
            assert await result.scalar() == 1
