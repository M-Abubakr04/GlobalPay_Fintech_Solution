from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.metrics import PAYMENTS
from app.models.entities import LedgerEntry, Transaction, Wallet
from app.modules.fraud.service import create_alert_if_needed, score_payment


def execute_transfer(
    db: Session,
    *,
    sender_wallet_id: str,
    receiver_wallet_id: str,
    amount: Decimal,
    description: str | None,
    idempotency_key: str,
    actor_user_id: str,
    correlation_id: str | None,
    channel: str = "WALLET_APP",
    transaction_type: str = "TRANSFER",
    merchant_risk: float = 0.1,
    new_device: bool = False,
) -> Transaction:
    existing = db.scalar(select(Transaction).where(Transaction.idempotency_key == idempotency_key))
    if existing:
        return existing
    if sender_wallet_id == receiver_wallet_id:
        raise HTTPException(status_code=400, detail="Sender and receiver wallets must be different")

    try:
        wallets = db.scalars(
            select(Wallet)
            .where(Wallet.id.in_([sender_wallet_id, receiver_wallet_id]))
            .order_by(Wallet.id)
            .with_for_update()
        ).all()
        by_id = {wallet.id: wallet for wallet in wallets}
        sender = by_id.get(sender_wallet_id)
        receiver = by_id.get(receiver_wallet_id)
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Sender or receiver wallet not found")
        if sender.status != "ACTIVE" or receiver.status != "ACTIVE":
            raise HTTPException(status_code=400, detail="Both wallets must be active")
        if sender.balance < amount:
            PAYMENTS.labels(status="FAILED", payment_type=transaction_type).inc()
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")

        result = score_payment(
            db,
            sender_wallet_id=sender.id,
            amount=amount,
            merchant_risk=merchant_risk,
            new_device=int(new_device),
        )

        transaction = Transaction(
            reference=f"GP-{uuid.uuid4().hex[:14].upper()}",
            sender_wallet_id=sender.id,
            receiver_wallet_id=receiver.id,
            amount=amount,
            currency=sender.currency,
            transaction_type=transaction_type,
            channel=channel,
            status="PROCESSING",
            description=description,
            idempotency_key=idempotency_key,
            risk_score=Decimal(str(result["score"])),
        )
        db.add(transaction)
        db.flush()

        sender.balance -= amount
        receiver.balance += amount
        db.add_all(
            [
                LedgerEntry(
                    transaction_id=transaction.id,
                    wallet_id=sender.id,
                    entry_type="DEBIT",
                    amount=amount,
                    balance_after=sender.balance,
                ),
                LedgerEntry(
                    transaction_id=transaction.id,
                    wallet_id=receiver.id,
                    entry_type="CREDIT",
                    amount=amount,
                    balance_after=receiver.balance,
                ),
            ]
        )
        transaction.status = "COMPLETED"
        create_alert_if_needed(db, transaction, result)
        record_audit(
            db,
            action="PAYMENT_COMPLETED",
            entity_type="transaction",
            entity_id=transaction.id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            metadata={
                "reference": transaction.reference,
                "amount": str(amount),
                "channel": channel,
                "risk_band": result["risk_band"],
            },
        )
        db.commit()
        db.refresh(transaction)
        PAYMENTS.labels(status="COMPLETED", payment_type=transaction_type).inc()
        return transaction
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(select(Transaction).where(Transaction.idempotency_key == idempotency_key))
        if duplicate:
            return duplicate
        raise
    except Exception:
        db.rollback()
        raise
