import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import record_audit
from app.core.database import get_db
from app.models.entities import Customer, LedgerEntry, Transaction, User, Wallet
from app.modules.wallets.schemas import BalanceAdjustment, WalletActivityOut, WalletOut

router = APIRouter(prefix="/wallets", tags=["Module 1 - Wallets"])


def wallet_for_user(db: Session, user: User) -> Wallet:
    customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
    wallet = db.scalar(select(Wallet).where(Wallet.customer_id == customer.id)) if customer else None
    if not wallet:
        raise HTTPException(status_code=404, detail="Customer wallet not found")
    return wallet


@router.get("/me", response_model=WalletOut)
def get_my_wallet(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = wallet_for_user(db, current_user)
    return WalletOut(
        id=wallet.id,
        balance=wallet.balance,
        currency=wallet.currency,
        status=wallet.status,
        owner_type="customer",
        created_at=wallet.created_at,
    )


@router.get("/me/activity", response_model=list[WalletActivityOut])
def get_activity(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = wallet_for_user(db, current_user)
    rows = db.execute(
        select(LedgerEntry, Transaction)
        .join(Transaction, Transaction.id == LedgerEntry.transaction_id)
        .where(LedgerEntry.wallet_id == wallet.id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(min(max(limit, 1), 200))
    ).all()
    return [
        WalletActivityOut(
            ledger_entry_id=entry.id,
            transaction_id=txn.id,
            reference=txn.reference,
            entry_type=entry.entry_type,
            amount=entry.amount,
            balance_after=entry.balance_after,
            status=txn.status,
            transaction_type=txn.transaction_type,
            description=txn.description,
            created_at=entry.created_at,
        )
        for entry, txn in rows
    ]


@router.post("/{wallet_id}/admin-adjust", response_model=WalletOut)
def admin_adjust_balance(
    wallet_id: str,
    payload: BalanceAdjustment,
    request: Request,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    try:
        wallet = db.scalar(select(Wallet).where(Wallet.id == wallet_id).with_for_update())
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        amount = Decimal(payload.amount)
        if payload.direction == "DEBIT" and wallet.balance < amount:
            raise HTTPException(status_code=400, detail="Adjustment would make balance negative")

        wallet.balance = wallet.balance + amount if payload.direction == "CREDIT" else wallet.balance - amount
        transaction = Transaction(
            reference=f"ADJ-{uuid.uuid4().hex[:12].upper()}",
            sender_wallet_id=wallet.id if payload.direction == "DEBIT" else None,
            receiver_wallet_id=wallet.id if payload.direction == "CREDIT" else None,
            amount=amount,
            transaction_type="ADJUSTMENT",
            channel="ADMIN",
            status="COMPLETED",
            description=payload.reason,
            idempotency_key=f"adjust-{uuid.uuid4()}",
        )
        db.add(transaction)
        db.flush()
        db.add(
            LedgerEntry(
                transaction_id=transaction.id,
                wallet_id=wallet.id,
                entry_type=payload.direction,
                amount=amount,
                balance_after=wallet.balance,
            )
        )
        record_audit(
            db,
            action="WALLET_BALANCE_ADJUSTED",
            entity_type="wallet",
            entity_id=wallet.id,
            actor_user_id=admin.id,
            correlation_id=getattr(request.state, "correlation_id", None),
            metadata={"direction": payload.direction, "amount": str(amount), "reason": payload.reason},
        )
        db.commit()
        return WalletOut(
            id=wallet.id,
            balance=wallet.balance,
            currency=wallet.currency,
            status=wallet.status,
            owner_type="customer" if wallet.customer_id else "merchant",
            created_at=wallet.created_at,
        )
    except Exception:
        db.rollback()
        raise

@router.get("/admin/list")
def admin_list_wallets(
    _: User = Depends(require_roles("admin", "executive")),
    db: Session = Depends(get_db),
):
    wallets = list(db.scalars(select(Wallet).order_by(Wallet.created_at.desc())))
    output = []
    for wallet in wallets:
        owner_name = "Unknown"
        owner_type = "customer" if wallet.customer_id else "merchant"
        if wallet.customer_id:
            customer = db.get(Customer, wallet.customer_id)
            owner_name = customer.full_name if customer else "Unknown customer"
        elif wallet.merchant_id:
            from app.models.entities import Merchant
            merchant = db.get(Merchant, wallet.merchant_id)
            owner_name = merchant.business_name if merchant else "Unknown merchant"
        output.append(
            {
                "id": wallet.id,
                "owner_name": owner_name,
                "owner_type": owner_type,
                "balance": wallet.balance,
                "currency": wallet.currency,
                "status": wallet.status,
                "created_at": wallet.created_at,
            }
        )
    return output
