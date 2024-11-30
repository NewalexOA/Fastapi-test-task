from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, InternalError, DataError
from asyncpg.exceptions import ConnectionDoesNotExistError
from decimal import Decimal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .models import Wallet, Transaction, TransactionStatus, OperationType

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
        .with_for_update()  # Add row-level lock
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, min=0.2, max=1),
    retry=retry_if_exception_type((OperationalError, InternalError, ConnectionDoesNotExistError)),
    retry_error_callback=lambda retry_state: retry_state.outcome.result(),
    reraise=True
)
async def update_wallet_balance(
    session: AsyncSession, 
    wallet_id: UUID,
    amount: Decimal,
    operation_type: OperationType
) -> Transaction:
    """Updates wallet balance and creates a transaction record"""
    try:
        async with session.begin_nested():
            wallet = await get_wallet_for_update(session, wallet_id)
            if not wallet:
                return None

            if operation_type == OperationType.WITHDRAW and wallet.balance < amount:
                transaction = Transaction(
                    wallet_id=wallet.id,
                    operation_type=operation_type,
                    amount=amount,
                    status=TransactionStatus.FAILED
                )
                session.add(transaction)
                await session.commit()
                raise ValueError("Insufficient funds")

            transaction = Transaction(
                wallet_id=wallet.id,
                operation_type=operation_type,
                amount=amount,
                status=TransactionStatus.PENDING
            )
            session.add(transaction)
            
            try:
                if operation_type == OperationType.DEPOSIT:
                    wallet.balance += amount
                else:
                    wallet.balance -= amount
                
                transaction.status = TransactionStatus.SUCCESS
                await session.commit()
            except Exception:
                transaction.status = TransactionStatus.FAILED
                await session.commit()
                raise
    except DataError:
        raise ValueError("Amount exceeds maximum allowed value")

    return transaction
