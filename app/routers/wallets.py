from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..database import get_session
from ..crud import create_wallet, get_wallet, update_wallet_balance
from ..schemas import TransactionCreate, WalletResponse, TransactionResponse
import logging

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
    try:
        transaction = await update_wallet_balance(
            session,
            wallet_id,
            operation.amount,
            operation.operation_type
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.exception("Error processing operation")
        raise HTTPException(status_code=500, detail="Internal server error")

