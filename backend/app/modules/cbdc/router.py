import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.metrics import OPEN_BANKING_CALLS
from app.models.entities import CbdcOperation, CbdcWallet, Customer, User
from app.modules.cbdc.schemas import CbdcIssueRequest, CbdcTransferRequest, CbdcWalletCreate

router = APIRouter(prefix="/cbdc", tags=["Module 4 - CBDC Simulation"])


@router.post("/wallets")
def create_wallet(
    payload: CbdcWalletCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
    wallet = CbdcWallet(
        customer_id=customer.id if customer else None,
        owner_label=payload.owner_label,
        balance=Decimal("0.00"),
        currency="ePKR",
    )
    db.add(wallet)
    db.flush()
    record_audit(
        db,
        action="CBDC_WALLET_CREATED",
        entity_type="cbdc_wallet",
        entity_id=wallet.id,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"simulation": True},
    )
    db.commit()
    OPEN_BANKING_CALLS.labels(endpoint="/cbdc/wallets", status="201").inc()
    return wallet


@router.get("/wallets")
def list_wallets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
    if current_user.role in {"admin", "executive", "analyst"}:
        query = select(CbdcWallet).order_by(CbdcWallet.created_at.desc())
    elif customer:
        query = (
            select(CbdcWallet)
            .where(CbdcWallet.customer_id == customer.id)
            .order_by(CbdcWallet.created_at.desc())
        )
    else:
        return []
    return list(db.scalars(query))




@router.get("/directory")
def cbdc_directory(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallets = list(
        db.scalars(
            select(CbdcWallet)
            .where(CbdcWallet.status == "ACTIVE")
            .order_by(CbdcWallet.owner_label)
        )
    )
    return [
        {
            "id": wallet.id,
            "owner_label": wallet.owner_label,
            "currency": wallet.currency,
            "status": wallet.status,
        }
        for wallet in wallets
    ]

@router.post("/issue")
def issue_currency(
    payload: CbdcIssueRequest,
    request: Request,
    operator: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    wallet = db.scalar(select(CbdcWallet).where(CbdcWallet.id == payload.wallet_id).with_for_update())
    if not wallet:
        raise HTTPException(status_code=404, detail="CBDC wallet not found")
    wallet.balance += payload.amount
    operation = CbdcOperation(
        reference=f"CBDC-{uuid.uuid4().hex[:12].upper()}",
        destination_wallet_id=wallet.id,
        operation_type="ISSUE",
        amount=payload.amount,
        status="COMPLETED",
    )
    db.add(operation)
    record_audit(
        db,
        action="CBDC_ISSUED",
        entity_type="cbdc_operation",
        entity_id=operation.id,
        actor_user_id=operator.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"amount": str(payload.amount), "simulation": True},
    )
    db.commit()
    return operation


@router.post("/transfer")
def transfer_currency(
    payload: CbdcTransferRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallets = db.scalars(
        select(CbdcWallet)
        .where(CbdcWallet.id.in_([payload.source_wallet_id, payload.destination_wallet_id]))
        .order_by(CbdcWallet.id)
        .with_for_update()
    ).all()
    by_id = {wallet.id: wallet for wallet in wallets}
    source = by_id.get(payload.source_wallet_id)
    destination = by_id.get(payload.destination_wallet_id)
    if not source or not destination:
        raise HTTPException(status_code=404, detail="CBDC source or destination wallet not found")
    if source.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient CBDC balance")
    source.balance -= payload.amount
    destination.balance += payload.amount
    operation = CbdcOperation(
        reference=f"CBDC-{uuid.uuid4().hex[:12].upper()}",
        source_wallet_id=source.id,
        destination_wallet_id=destination.id,
        operation_type="TRANSFER",
        amount=payload.amount,
        status="COMPLETED",
    )
    db.add(operation)
    record_audit(
        db,
        action="CBDC_TRANSFER_COMPLETED",
        entity_type="cbdc_operation",
        entity_id=operation.id,
        actor_user_id=current_user.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"amount": str(payload.amount), "simulation": True},
    )
    db.commit()
    return operation


@router.get("/analytics")
def analytics(
    _: User = Depends(require_roles("admin", "executive", "analyst")),
    db: Session = Depends(get_db),
):
    wallet_count = db.scalar(select(func.count(CbdcWallet.id))) or 0
    operations = db.scalar(select(func.count(CbdcOperation.id))) or 0
    issued = db.scalar(
        select(func.coalesce(func.sum(CbdcOperation.amount), 0))
        .where(CbdcOperation.operation_type == "ISSUE")
    ) or 0
    return {
        "wallet_count": wallet_count,
        "operation_count": operations,
        "total_issued": issued,
        "currency": "ePKR",
    }
