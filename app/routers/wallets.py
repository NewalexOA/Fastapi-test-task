from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..database import get_session
from ..crud import create_wallet, get_wallet, update_wallet_balance
from ..schemas import TransactionCreate, WalletResponse, TransactionResponse, TransactionStatus
import logging
from sqlalchemy.exc import DataError, OperationalError
from asyncpg.exceptions import LockNotAvailableError
import asyncio
from datetime import datetime
from uuid import uuid4

router = APIRouter()

@router.post("/", response_model=WalletResponse)
async def create_new_wallet(session: AsyncSession = Depends(get_session)):
    """Create a new wallet with zero balance"""
    wallet = await create_wallet(session)
    return wallet

@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet_info(wallet_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get wallet information"""
    wallet = await get_wallet(session, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.post("/{wallet_id}/operation", response_model=TransactionResponse)
async def process_operation(
    wallet_id: UUID,
    operation: TransactionCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        updated_wallet, amount = await update_wallet_balance(
            wallet_id=wallet_id,
            amount=operation.amount,
            operation_type=operation.operation_type,
            session=session
        )
        
        return TransactionResponse(
            id=uuid4(),
            wallet_id=wallet_id,
            amount=amount,
            operation_type=operation.operation_type,
            status=TransactionStatus.SUCCESS,
            created_at=datetime.utcnow()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in process_operation: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Internal server error. Please try again later."
        )

