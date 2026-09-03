from decimal import Decimal

from pydantic import BaseModel, Field


class CbdcWalletCreate(BaseModel):
    owner_label: str = Field(min_length=2, max_length=180)


class CbdcIssueRequest(BaseModel):
    wallet_id: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class CbdcTransferRequest(BaseModel):
    source_wallet_id: str
    destination_wallet_id: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
