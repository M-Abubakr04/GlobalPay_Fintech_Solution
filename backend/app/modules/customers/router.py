from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import decrypt_pii, encrypt_pii
from app.models.entities import Customer, Merchant, Transaction, User, Wallet
from app.modules.customers.schemas import (
    CustomerProfileOut,
    CustomerReportOut,
    CustomerUpdate,
    MerchantApplication,
    MerchantPaymentOut,
    MerchantSettlementReportOut,
)

router = APIRouter(prefix="/customers", tags=["Module 1 - Customers"])


def customer_for_user(db: Session, user_id: str) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.user_id == user_id))
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return customer


def _mask(value: str | None, visible: int = 2) -> str | None:
    if not value:
        return None
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


@router.get("/me", response_model=CustomerProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = customer_for_user(db, current_user.id)
    return CustomerProfileOut(
        id=customer.id,
        email=current_user.email,
        full_name=customer.full_name,
        phone_masked=_mask(decrypt_pii(customer.phone_encrypted), 3),
        national_id_masked=_mask(decrypt_pii(customer.national_id_encrypted), 2),
        kyc_status=customer.kyc_status,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


@router.put("/me", response_model=CustomerProfileOut)
def update_profile(
    payload: CustomerUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = customer_for_user(db, current_user.id)
    if payload.full_name is not None:
        customer.full_name = payload.full_name.strip()
    if payload.phone is not None:
        customer.phone_encrypted = encrypt_pii(payload.phone)
    if payload.national_id is not None:
        customer.national_id_encrypted = encrypt_pii(payload.national_id)

    record_audit(
        db,
        action="CUSTOMER_PROFILE_UPDATED",
        entity_type="customer",
        entity_id=customer.id,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"fields_changed": [k for k, v in payload.model_dump().items() if v is not None]},
    )
    db.commit()
    return get_profile(current_user, db)


@router.post("/merchant-application")
def create_merchant_application(
    payload: MerchantApplication,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Merchant).where(Merchant.user_id == current_user.id))
    if existing:
        return {"merchant_id": existing.id, "status": existing.status, "message": "Application already exists"}

    merchant = Merchant(user_id=current_user.id, business_name=payload.business_name, status="PENDING")
    db.add(merchant)
    db.flush()
    wallet = Wallet(merchant_id=merchant.id, balance=0, currency="PKR", status="ACTIVE")
    db.add(wallet)
    record_audit(
        db,
        action="MERCHANT_APPLICATION_CREATED",
        entity_type="merchant",
        entity_id=merchant.id,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"settlement_wallet_created": True},
    )
    db.commit()
    return {"merchant_id": merchant.id, "wallet_id": wallet.id, "status": merchant.status}


@router.get("/me/report", response_model=CustomerReportOut)
def customer_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = customer_for_user(db, current_user.id)
    wallet = db.scalar(select(Wallet).where(Wallet.customer_id == customer.id))
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    tx_count = db.scalar(
        select(func.count(Transaction.id)).where(
            or_(Transaction.sender_wallet_id == wallet.id, Transaction.receiver_wallet_id == wallet.id)
        )
    ) or 0
    total_sent = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.sender_wallet_id == wallet.id,
            Transaction.status == "COMPLETED",
        )
    ) or Decimal("0")
    total_received = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.receiver_wallet_id == wallet.id,
            Transaction.status == "COMPLETED",
        )
    ) or Decimal("0")
    merchant = db.scalar(select(Merchant).where(Merchant.user_id == current_user.id))

    return CustomerReportOut(
        customer_id=customer.id,
        wallet_id=wallet.id,
        balance=wallet.balance,
        currency=wallet.currency,
        transaction_count=tx_count,
        total_sent=total_sent,
        total_received=total_received,
        merchant_status=merchant.status if merchant else None,
    )




@router.get("/merchant/me/report", response_model=MerchantSettlementReportOut)
def merchant_settlement_report(
    current_user: User = Depends(require_roles("merchant")),
    db: Session = Depends(get_db),
):
    merchant = db.scalar(select(Merchant).where(Merchant.user_id == current_user.id))
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant profile not found")
    wallet = db.scalar(select(Wallet).where(Wallet.merchant_id == merchant.id))
    if not wallet:
        raise HTTPException(status_code=404, detail="Merchant settlement wallet not found")

    completed_filter = (
        Transaction.receiver_wallet_id == wallet.id,
        Transaction.status == "COMPLETED",
    )
    payment_count = db.scalar(select(func.count(Transaction.id)).where(*completed_filter)) or 0
    payment_volume = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(*completed_filter)
    ) or Decimal(0)
    payments = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.receiver_wallet_id == wallet.id)
            .order_by(Transaction.created_at.desc())
            .limit(100)
        )
    )

    return MerchantSettlementReportOut(
        merchant_id=merchant.id,
        business_name=merchant.business_name,
        status=merchant.status,
        settlement_cycle=merchant.settlement_config.get("cycle", "T+1"),
        wallet_id=wallet.id,
        wallet_status=wallet.status,
        balance=wallet.balance,
        currency=wallet.currency,
        completed_payment_count=payment_count,
        completed_payment_volume=payment_volume,
        payments=[MerchantPaymentOut.model_validate(payment, from_attributes=True) for payment in payments],
    )


@router.get("/merchants/active")
def list_active_merchants(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchants = list(
        db.scalars(
            select(Merchant)
            .where(Merchant.status.in_(["ACTIVE", "APPROVED"]))
            .order_by(Merchant.business_name)
        )
    )
    return [
        {
            "merchant_id": merchant.id,
            "business_name": merchant.business_name,
            "status": merchant.status,
            "settlement_cycle": merchant.settlement_config.get("cycle", "T+1"),
        }
        for merchant in merchants
    ]

@router.get("/admin/list")
def list_customers(
    _: User = Depends(require_roles("admin", "executive")),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Customer, User).join(User, User.id == Customer.user_id).order_by(Customer.created_at.desc())
    ).all()
    return [
        {
            "customer_id": customer.id,
            "name": customer.full_name,
            "email": user.email,
            "kyc_status": customer.kyc_status,
            "active": customer.is_active,
            "created_at": customer.created_at,
        }
        for customer, user in rows
    ]
