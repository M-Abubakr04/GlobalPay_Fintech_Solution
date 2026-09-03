from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    national_id: str | None = Field(default=None, max_length=60)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegistrationResponse(BaseModel):
    user: UserOut
    customer_id: str
    wallet_id: str
    message: str
