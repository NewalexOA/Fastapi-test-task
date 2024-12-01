from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from asyncpg.exceptions import ConnectionDoesNotExistError
from decimal import Decimal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from fastapi import HTTPException
import asyncio
from sqlalchemy.exc import SQLAlchemyError

from .models import Wallet, OperationType

async def create_wallet(session: AsyncSession) -> Wallet:
    """Creates a new wallet with zero balance"""
    wallet = Wallet()
    session.add(wallet)
    await session.commit()
    return wallet

async def get_wallet(session: AsyncSession, wallet_id: UUID) -> Wallet | None:
    """Gets wallet information by its ID"""
    query = (
        select(Wallet)
        .where(Wallet.id == wallet_id)
        .execution_options(populate_existing=True)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def get_wallet_for_update(session: AsyncSession, wallet_id: UUID) -> Wallet | None:
    """Gets wallet with row-level lock for update"""
    query = (
        select(Wallet)
        .where(Wallet.id == wallet_id)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1),
    retry=retry_if_exception_type((OperationalError, ConnectionDoesNotExistError))
)
async def update_wallet_balance(
    wallet_id: UUID,
    amount: Decimal,
    operation_type: OperationType,
    session: AsyncSession,
    max_retries: int = 3
) -> tuple[Wallet, Decimal]:
    for attempt in range(max_retries):
        try:
            wallet = await session.get(Wallet, wallet_id)
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")
                
            new_balance = wallet.balance + amount if operation_type == OperationType.DEPOSIT else wallet.balance - amount
            
            if new_balance < 0:
                raise HTTPException(status_code=400, 
                                  detail="Insufficient funds or operation cannot be processed")
                
            wallet.balance = new_balance
            await session.commit()
            return wallet, amount
            
        except SQLAlchemyError:
            await session.rollback()
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, 
                                  detail="Service temporarily unavailable")
            await asyncio.sleep(0.1 * (attempt + 1))
