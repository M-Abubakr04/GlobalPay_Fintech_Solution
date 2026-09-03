from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class TransferRequest(BaseModel):
    receiver_email: EmailStr | None = None
    receiver_wallet_id: str | None = None
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)
    new_device: bool = False

    @model_validator(mode="after")
    def receiver_required(self):
        if not self.receiver_email and not self.receiver_wallet_id:
            raise ValueError("receiver_email or receiver_wallet_id is required")
        return self


class MerchantPaymentRequest(BaseModel):
    merchant_id: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)


class TransactionOut(BaseModel):
    id: str
    reference: str
    sender_wallet_id: str | None
    receiver_wallet_id: str | None
    amount: Decimal
    currency: str
    transaction_type: str
    channel: str
    status: str
    description: str | None
    risk_score: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentDashboardOut(BaseModel):
    transaction_count: int
    completed_count: int
    failed_count: int
    under_review_count: int
    total_volume: Decimal
    recent_transactions: list[TransactionOut]
