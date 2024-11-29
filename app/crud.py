from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from .models import Wallet, Transaction, TransactionStatus, OperationType

async def create_wallet(session: AsyncSession) -> Wallet:
    """Creates a new wallet with zero balance"""
    wallet = Wallet()
    session.add(wallet)
    await session.commit()
    return wallet

async def get_wallet(session: AsyncSession, wallet_id: UUID) -> Wallet | None:
    """Gets wallet information by its ID"""
    query = select(Wallet).where(Wallet.id == wallet_id)
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

async def update_wallet_balance(
    session: AsyncSession, 
    wallet_id: UUID,
    amount: Decimal,
    operation_type: OperationType
) -> Transaction:
    """Updates wallet balance and creates a transaction record"""
    # Get wallet with lock
    wallet = await get_wallet_for_update(session, wallet_id)
    if not wallet:
        return None

    # Validate balance for withdrawal
    if operation_type == OperationType.WITHDRAW and wallet.balance < amount:
        raise ValueError("Insufficient funds")

    # Create transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        operation_type=operation_type,
        amount=amount,
        status=TransactionStatus.PENDING
    )
    session.add(transaction)
    
    try:
        # Update balance
        if operation_type == OperationType.DEPOSIT:
            wallet.balance += amount
        else:  # WITHDRAW
            wallet.balance -= amount
        
        # Confirm transaction
        transaction.status = TransactionStatus.SUCCESS
        await session.commit()
    except Exception as e:
        # Mark transaction as failed
        transaction.status = TransactionStatus.FAILED
        await session.commit()
        raise Exception(f"Failed to update wallet balance: {str(e)}") from e

    return transaction
