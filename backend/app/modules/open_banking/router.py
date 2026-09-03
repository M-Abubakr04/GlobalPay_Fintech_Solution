import time
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.metrics import OPEN_BANKING_CALLS
from app.models.entities import ApiCall, Consent, Customer, User, Wallet
from app.modules.open_banking.schemas import ConsentCreate, PisPaymentRequest
from app.modules.payments.service import execute_transfer

router = APIRouter(prefix="/open-banking", tags=["Module 4 - Open Banking"])


def customer_for_user(db: Session, user_id: str) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.user_id == user_id))
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return customer


def validate_consent(db: Session, consent_id: str, customer_id: str, required_scope: str) -> Consent:
    consent = db.get(Consent, consent_id)
    if not consent or consent.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Consent not found")
    expires_at = consent.expires_at
    if expires_at.tzinfo is None:
        # SQLite drops timezone metadata in tests; PostgreSQL keeps TIMESTAMPTZ aware.
        expires_at = expires_at.replace(tzinfo=UTC)
    if consent.status != "ACTIVE" or expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=403, detail="Consent is inactive or expired")
    if required_scope not in consent.scopes:
        raise HTTPException(status_code=403, detail=f"Consent does not include {required_scope}")
    return consent


def log_call(db: Session, consent_id: str | None, endpoint: str, status_code: int, started: float):
    latency = Decimal(str(round((time.perf_counter() - started) * 1000, 2)))
    db.add(
        ApiCall(
            consent_id=consent_id,
            endpoint=endpoint,
            method="POST" if "payments" in endpoint else "GET",
            status_code=status_code,
            latency_ms=latency,
        )
    )
    OPEN_BANKING_CALLS.labels(endpoint=endpoint, status=str(status_code)).inc()


@router.post("/consents")
def create_consent(
    payload: ConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {"accounts:read", "payments:write", "cbdc:read", "cbdc:write"}
    invalid = set(payload.scopes) - allowed
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported scopes: {sorted(invalid)}")
    customer = customer_for_user(db, current_user.id)
    consent = Consent(
        customer_id=customer.id,
        client_name=payload.client_name,
        scopes=payload.scopes,
        status="ACTIVE",
        expires_at=datetime.now(UTC) + timedelta(hours=payload.expires_in_hours),
    )
    db.add(consent)
    db.flush()
    record_audit(
        db,
        action="OPEN_BANKING_CONSENT_CREATED",
        entity_type="consent",
        entity_id=consent.id,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"client_name": payload.client_name, "scopes": payload.scopes},
    )
    db.commit()
    return consent


@router.get("/consents")
def list_consents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = customer_for_user(db, current_user.id)
    return list(
        db.scalars(
            select(Consent)
            .where(Consent.customer_id == customer.id)
            .order_by(Consent.created_at.desc())
        )
    )


@router.get("/ais/accounts/{wallet_id}")
def account_information(
    wallet_id: str,
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = time.perf_counter()
    customer = customer_for_user(db, current_user.id)
    consent = validate_consent(db, consent_id, customer.id, "accounts:read")
    wallet = db.get(Wallet, wallet_id)
    if not wallet or wallet.customer_id != customer.id:
        log_call(db, consent.id, "/ais/accounts", 404, started)
        db.commit()
        raise HTTPException(status_code=404, detail="Account not found")
    response = {
        "account_id": wallet.id,
        "currency": wallet.currency,
        "available_balance": wallet.balance,
        "status": wallet.status,
        "message_standard": "ISO 20022-inspired field naming for simulation",
    }
    log_call(db, consent.id, "/ais/accounts", 200, started)
    db.commit()
    return response


@router.post("/pis/payments")
def payment_initiation(
    payload: PisPaymentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = time.perf_counter()
    customer = customer_for_user(db, current_user.id)
    consent = validate_consent(db, payload.consent_id, customer.id, "payments:write")
    sender = db.scalar(select(Wallet).where(Wallet.customer_id == customer.id))
    if not sender:
        raise HTTPException(status_code=404, detail="Source wallet not found")
    if payload.receiver_wallet_id:
        receiver = db.get(Wallet, payload.receiver_wallet_id)
    else:
        receiver = db.scalar(
            select(Wallet)
            .join(Customer, Customer.id == Wallet.customer_id)
            .join(User, User.id == Customer.user_id)
            .where(User.email == str(payload.receiver_email).lower())
        )
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver wallet not found")

    transaction = execute_transfer(
        db,
        sender_wallet_id=sender.id,
        receiver_wallet_id=receiver.id,
        amount=payload.amount,
        description=payload.description,
        idempotency_key=f"pis-{uuid.uuid4()}",
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        channel="OPEN_BANKING_PIS",
        transaction_type="PIS_PAYMENT",
    )
    # The payment service commits the financial transaction; log API evidence separately.
    log_call(db, consent.id, "/pis/payments", 200, started)
    db.commit()
    return {"payment_id": transaction.id, "reference": transaction.reference, "status": transaction.status}


@router.get("/analytics")
def api_analytics(
    _: User = Depends(require_roles("admin", "executive", "analyst")),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ApiCall.endpoint, func.count(ApiCall.id), func.avg(ApiCall.latency_ms))
        .group_by(ApiCall.endpoint)
        .order_by(func.count(ApiCall.id).desc())
    ).all()
    return [
        {"endpoint": endpoint, "calls": count, "average_latency_ms": round(float(avg or 0), 2)}
        for endpoint, count, avg in rows
    ]


@router.get("/health")
def api_health(db: Session = Depends(get_db)):
    calls = db.scalar(select(func.count(ApiCall.id))) or 0
    failures = db.scalar(select(func.count(ApiCall.id)).where(ApiCall.status_code >= 400)) or 0
    return {
        "status": "healthy",
        "total_calls": calls,
        "failed_calls": failures,
        "success_rate": round(((calls - failures) / calls * 100), 2) if calls else 100.0,
    }
