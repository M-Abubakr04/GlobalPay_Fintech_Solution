import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.cache import cache_get_json, cache_set_json
from app.core.database import get_db
from app.models.entities import Customer, Merchant, Transaction, User, Wallet
from app.modules.payments.schemas import (
    MerchantPaymentRequest,
    PaymentDashboardOut,
    TransactionOut,
    TransferRequest,
)
from app.modules.payments.service import execute_transfer
from app.modules.wallets.router import wallet_for_user

router = APIRouter(prefix="/payments", tags=["Module 2 - Payments"])


def resolve_receiver_wallet(db: Session, payload: TransferRequest) -> Wallet:
    if payload.receiver_wallet_id:
        wallet = db.scalar(select(Wallet).where(Wallet.id == payload.receiver_wallet_id))
    else:
        wallet = db.scalar(
            select(Wallet)
            .join(Customer, Customer.id == Wallet.customer_id)
            .join(User, User.id == Customer.user_id)
            .where(User.email == str(payload.receiver_email).lower())
        )
    if not wallet:
        raise HTTPException(status_code=404, detail="Receiver wallet not found")
    return wallet


@router.post("/transfer", response_model=TransactionOut)
def transfer(
    payload: TransferRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sender = wallet_for_user(db, current_user)
    receiver = resolve_receiver_wallet(db, payload)
    key = idempotency_key or str(uuid.uuid4())
    cached = cache_get_json(f"idempotency:{key}")
    if cached:
        existing = db.get(Transaction, cached.get("transaction_id"))
        if existing:
            return existing

    transaction = execute_transfer(
        db,
        sender_wallet_id=sender.id,
        receiver_wallet_id=receiver.id,
        amount=Decimal(payload.amount),
        description=payload.description,
        idempotency_key=key,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        new_device=payload.new_device,
    )
    cache_set_json(f"idempotency:{key}", {"transaction_id": transaction.id}, ttl_seconds=86400)
    return transaction


@router.post("/merchant-charge", response_model=TransactionOut)
def merchant_charge(
    payload: MerchantPaymentRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sender = wallet_for_user(db, current_user)
    merchant = db.get(Merchant, payload.merchant_id)
    if not merchant or merchant.status not in {"ACTIVE", "APPROVED"}:
        raise HTTPException(status_code=404, detail="Approved merchant not found")
    receiver = db.scalar(select(Wallet).where(Wallet.merchant_id == merchant.id))
    if not receiver:
        raise HTTPException(status_code=404, detail="Merchant settlement wallet not found")
    return execute_transfer(
        db,
        sender_wallet_id=sender.id,
        receiver_wallet_id=receiver.id,
        amount=Decimal(payload.amount),
        description=payload.description or f"Payment to {merchant.business_name}",
        idempotency_key=idempotency_key or str(uuid.uuid4()),
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        channel="MERCHANT_PORTAL",
        transaction_type="MERCHANT_PAYMENT",
        merchant_risk=0.15,
    )


@router.get("/history", response_model=list[TransactionOut])
def history(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = wallet_for_user(db, current_user)
    return list(
        db.scalars(
            select(Transaction)
            .where(or_(Transaction.sender_wallet_id == wallet.id, Transaction.receiver_wallet_id == wallet.id))
            .order_by(Transaction.created_at.desc())
            .limit(min(max(limit, 1), 500))
        )
    )


@router.get("/dashboard", response_model=PaymentDashboardOut)
def payment_dashboard(
    _: User = Depends(require_roles("admin", "executive", "analyst")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(Transaction.id))) or 0
    completed = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "COMPLETED")) or 0
    failed = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "FAILED")) or 0
    under_review = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.risk_score >= Decimal("0.7000"))
    ) or 0
    volume = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.status == "COMPLETED")
    ) or Decimal("0")
    recent = list(db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(10)))
    return PaymentDashboardOut(
        transaction_count=total,
        completed_count=completed,
        failed_count=failed,
        under_review_count=under_review,
        total_volume=volume,
        recent_transactions=recent,
    )


@router.get("/reports/financial")
def financial_report(
    _: User = Depends(require_roles("admin", "executive")),
    db: Session = Depends(get_db),
):
    by_type = db.execute(
        select(
            Transaction.transaction_type,
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .where(Transaction.status == "COMPLETED")
        .group_by(Transaction.transaction_type)
    ).all()
    return {
        "currency": "PKR",
        "breakdown": [
            {"transaction_type": row[0], "count": row[1], "volume": row[2]} for row in by_type
        ],
    }
