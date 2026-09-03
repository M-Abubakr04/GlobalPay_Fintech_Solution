from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletOut(BaseModel):
    id: str
    balance: Decimal
    currency: str
    status: str
    owner_type: str
    created_at: datetime


class WalletActivityOut(BaseModel):
    ledger_entry_id: str
    transaction_id: str
    reference: str
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    status: str
    transaction_type: str
    description: str | None
    created_at: datetime


class BalanceAdjustment(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    direction: str = Field(pattern="^(CREDIT|DEBIT)$")
    reason: str = Field(min_length=3, max_length=255)
