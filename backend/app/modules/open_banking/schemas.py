from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class ConsentCreate(BaseModel):
    client_name: str = Field(min_length=2, max_length=150)
    scopes: list[str] = Field(min_length=1)
    expires_in_hours: int = Field(default=24, ge=1, le=720)


class PisPaymentRequest(BaseModel):
    consent_id: str
    receiver_wallet_id: str | None = None
    receiver_email: EmailStr | None = None
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: str | None = Field(default="Open Banking PIS payment", max_length=255)

    @model_validator(mode="after")
    def receiver_is_present(self):
        if not self.receiver_wallet_id and not self.receiver_email:
            raise ValueError("receiver_wallet_id or receiver_email is required")
        return self
