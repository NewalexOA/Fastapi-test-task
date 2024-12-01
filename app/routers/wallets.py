from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..database import get_session
from ..crud import create_wallet, get_wallet, update_wallet_balance
from ..schemas import TransactionCreate, WalletResponse, TransactionResponse
import logging
from sqlalchemy.exc import DataError, OperationalError
from asyncpg.exceptions import LockNotAvailableError
import asyncio

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
    """Process deposit or withdrawal operation"""
    for attempt in range(3):
        try:
            transaction = await update_wallet_balance(
                session,
                wallet_id,
                operation.amount,
                operation.operation_type
            )
            if not transaction:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient funds or operation cannot be processed"
                )
            return transaction
        except OperationalError as e:
            logging.error(f"Database operational error: {str(e)}")
            await session.rollback()
            if attempt == 2:
                raise HTTPException(
                    status_code=503, 
                    detail="Service temporarily unavailable"
                )
            await asyncio.sleep(0.1 * (attempt + 1))
        except LockNotAvailableError as e:
            logging.error(f"Lock acquisition failed: {str(e)}")
            await session.rollback()
            if attempt == 2:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable due to lock contention"
                )
            await asyncio.sleep(0.1 * (attempt + 1))
        except DataError as e:
            logging.error(f"Data error: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=400, detail="Invalid operation data")
        except Exception as e:
            logging.error(f"Unexpected error in process_operation: {str(e)}", exc_info=True)
            await session.rollback()
            raise HTTPException(
                status_code=500, 
                detail="Internal server error. Please try again later."
            )

