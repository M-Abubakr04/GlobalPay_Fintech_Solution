from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import create_access_token, encrypt_pii, hash_password, verify_password
from app.models.entities import Customer, User, Wallet
from app.modules.auth.schemas import RegisterRequest, RegistrationResponse, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")

    try:
        user = User(email=email, password_hash=hash_password(payload.password), role="customer")
        db.add(user)
        db.flush()

        customer = Customer(
            user_id=user.id,
            full_name=payload.full_name.strip(),
            phone_encrypted=encrypt_pii(payload.phone),
            national_id_encrypted=encrypt_pii(payload.national_id),
            kyc_status="PENDING",
        )
        db.add(customer)
        db.flush()

        wallet = Wallet(customer_id=customer.id, balance=0, currency="PKR", status="ACTIVE")
        db.add(wallet)
        db.flush()

        record_audit(
            db,
            action="CUSTOMER_REGISTERED",
            entity_type="customer",
            entity_id=customer.id,
            actor_user_id=user.id,
            correlation_id=getattr(request.state, "correlation_id", None),
            metadata={"wallet_created": True, "kyc_status": customer.kyc_status},
        )
        db.commit()
        db.refresh(user)
        return RegistrationResponse(
            user=user,
            customer_id=customer.id,
            wallet_id=wallet.id,
            message="Customer registered and digital wallet created successfully.",
        )
    except Exception:
        db.rollback()
        raise


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form.username.lower().strip()
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
