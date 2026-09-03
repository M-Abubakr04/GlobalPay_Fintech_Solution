from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ManualScoreRequest(BaseModel):
    sender_wallet_id: str
    amount: Decimal = Field(gt=0)
    merchant_risk: float = Field(default=0.1, ge=0, le=1)
    new_device: bool = False


class AlertOut(BaseModel):
    id: str
    transaction_id: str
    transaction_reference: str
    risk_score: Decimal
    confidence: Decimal
    risk_band: str
    status: str
    reasons: list[str]
    created_at: datetime


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(CONFIRMED_FRAUD|LEGITIMATE|ESCALATED)$")
    notes: str = Field(min_length=3, max_length=2000)
