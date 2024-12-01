from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from asyncpg.exceptions import ConnectionDoesNotExistError, TooManyConnectionsError
from decimal import Decimal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple
import logging

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
    session: AsyncSession, 
    wallet_id: UUID,
    operation_type: OperationType,
    amount: Decimal
) -> Tuple[Wallet, Decimal]:
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
        
    except TooManyConnectionsError:
        await session.rollback()
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again later."
        )
    except OperationalError as e:
        await session.rollback()
        logging.error(f"Database operational error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable due to database error"
        )
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
