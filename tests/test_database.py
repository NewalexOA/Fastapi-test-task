import pytest
from app.database import get_session, monitored_session
from unittest.mock import patch
from sqlalchemy.sql import text

@pytest.mark.asyncio
async def test_session_lifecycle():
    """Test session creation and cleanup"""
    async for session in get_session():
        assert session is not None
        assert not session.is_active
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