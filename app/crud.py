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
    amount: Decimal,
    operation_type: OperationType
) -> Transaction | None:
    """Updates wallet balance and creates transaction record"""
    try:
        async with session.begin():
            # First acquire lock on the wallet
            query = (
                select(Wallet)
                .where(Wallet.id == wallet_id)
                .with_for_update()
            )
            
            wallet = await session.execute(query)
            wallet = wallet.scalar_one_or_none()
            
            if not wallet:
                return None

            # Check for an existing successful withdrawal transaction under the lock
            if operation_type == OperationType.WITHDRAW:
                existing_transaction = await session.execute(
                    select(Transaction)
                    .where(
                        Transaction.wallet_id == wallet_id,
                        Transaction.operation_type == OperationType.WITHDRAW,
                        Transaction.status == TransactionStatus.SUCCESS
                    )
                )
                if existing_transaction.scalar_one_or_none():
                    return None

            if operation_type == OperationType.WITHDRAW and wallet.balance < amount:
                raise ValueError("Insufficient funds")

            if operation_type == OperationType.DEPOSIT:
                wallet.balance += amount
            else:
                wallet.balance -= amount

            transaction = Transaction(
                wallet_id=wallet_id,
                operation_type=operation_type,
                amount=amount,
                status=TransactionStatus.SUCCESS
            )
            session.add(transaction)
            
            return transaction
            
    except Exception:
        await session.rollback()
        raise
