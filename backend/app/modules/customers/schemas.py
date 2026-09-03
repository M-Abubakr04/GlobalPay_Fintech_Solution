from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CustomerProfileOut(BaseModel):
    id: str
    email: str
    full_name: str
    phone_masked: str | None
    national_id_masked: str | None
    kyc_status: str
    is_active: bool
    created_at: datetime


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    national_id: str | None = Field(default=None, max_length=60)


class MerchantApplication(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)


class CustomerReportOut(BaseModel):
    customer_id: str
    wallet_id: str
    balance: Decimal
    currency: str
    transaction_count: int
    total_sent: Decimal
    total_received: Decimal
    merchant_status: str | None
