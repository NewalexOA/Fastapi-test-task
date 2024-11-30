from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from .models import OperationType, TransactionStatus

class WalletBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class WalletCreate(WalletBase):
    pass

class WalletResponse(WalletBase):
    id: UUID
    balance: Decimal = Field(decimal_places=2)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: f"{float(v):.2f}"
        }
    )

class TransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TransactionCreate(TransactionBase):
    operation_type: OperationType
    amount: Decimal = Field(gt=0, le=Decimal('9999999999999999.99'))

class TransactionResponse(TransactionBase):
    id: UUID
    wallet_id: UUID
    operation_type: OperationType
    amount: Decimal
    status: TransactionStatus
    created_at: datetime
