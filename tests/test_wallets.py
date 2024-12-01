import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.main import app
from unittest.mock import patch
import asyncio
from sqlalchemy.exc import DataError, OperationalError
import random

@pytest.mark.asyncio
async def test_create_wallet():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/wallets/")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["balance"] == "0.00"

@pytest.mark.asyncio
async def test_get_nonexistent_wallet():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/wallets/{uuid4()}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Wallet not found"

@pytest.mark.asyncio
async def test_deposit_withdraw():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create wallet
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        # Deposit
        deposit_response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "DEPOSIT",
                "amount": "100.00"
            }
        )
        assert deposit_response.status_code == 200
        assert deposit_response.json()["status"] == "SUCCESS"
        
        # Check balance
        wallet = await client.get(f"/api/v1/wallets/{wallet_id}")
        assert wallet.json()["balance"] == "100.00"
        
        # Withdraw
        withdraw_response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "WITHDRAW",
                "amount": "50.00"
            }
        )
        assert withdraw_response.status_code == 200
        assert withdraw_response.json()["status"] == "SUCCESS"
        
        # Check final balance
        wallet = await client.get(f"/api/v1/wallets/{wallet_id}")
        assert wallet.json()["balance"] == "50.00"

@pytest.mark.asyncio
async def test_insufficient_funds():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create wallet
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        # Try to withdraw
        withdraw_response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "WITHDRAW",
                "amount": "100.00"
            }
        )
        assert withdraw_response.status_code == 400
        assert "Insufficient funds" in withdraw_response.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_amount():
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        # Try with negative amount
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "DEPOSIT",
                "amount": "-100.00"
            }
        )
        assert response.status_code == 422
        
        # Try with too large amount
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "DEPOSIT",
                "amount": "999999999999999999.99"
            }
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_transaction_rollback():
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        with patch("app.routers.wallets.update_wallet_balance", autospec=True) as mock_update:
            mock_update.side_effect = DataError("statement", {}, "Database error")
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation_type": "DEPOSIT",
                    "amount": "100.00"
                }
            )
            assert response.status_code == 200
            assert response.json()["status"] == "FAILED"

@pytest.mark.asyncio
async def test_concurrent_operations():
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        # Initial deposit
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "100.00"}
        )
        
        async def withdraw():
            await asyncio.sleep(random.uniform(0.1, 0.3))
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": "50.00"}
            )
            return response.json()["status"] == "SUCCESS"
        
        responses = await asyncio.gather(
            *[withdraw() for _ in range(3)],
            return_exceptions=True
        )
        
        success_count = sum(1 for r in responses if r is True)
        assert success_count == 2

@pytest.mark.asyncio
async def test_internal_server_error():
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        with patch("app.routers.wallets.update_wallet_balance", autospec=True) as mock_update:
            mock_update.side_effect = Exception("Unexpected error")
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation_type": "DEPOSIT",
                    "amount": "100.00"
                }
            )
            assert response.status_code == 200
            assert response.json()["status"] == "FAILED"

@pytest.mark.asyncio
async def test_database_errors():
    """Test database connection errors"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        with patch("app.routers.wallets.update_wallet_balance", autospec=True) as mock:
            mock.side_effect = OperationalError("statement", {}, None)
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation_type": "DEPOSIT",
                    "amount": "100.00"
                }
            )
            assert response.status_code == 200
            assert response.json()["status"] == "FAILED"

@pytest.mark.asyncio
async def test_service_unavailable():
    """Test that service unavailability returns FAILED status instead of 503"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        wallet_response = await client.post("/api/v1/wallets/")
        wallet_id = wallet_response.json()["id"]
        
        with patch("app.routers.wallets.update_wallet_balance", autospec=True) as mock:
            mock.side_effect = OperationalError("statement", {}, None)
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation_type": "DEPOSIT",
                    "amount": "100.00"
                }
            )
            assert response.status_code == 200
            assert response.json()["status"] == "FAILED"
    