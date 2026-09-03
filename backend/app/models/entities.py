from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone_encrypted: Mapped[str | None] = mapped_column(Text)
    national_id_encrypted: Mapped[str | None] = mapped_column(Text)
    kyc_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    settlement_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallet_balance_nonnegative"),
        CheckConstraint(
            "(customer_id IS NOT NULL AND merchant_id IS NULL) OR "
            "(customer_id IS NULL AND merchant_id IS NOT NULL)",
            name="ck_wallet_exactly_one_owner",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), unique=True, index=True)
    merchant_id: Mapped[str | None] = mapped_column(ForeignKey("merchants.id"), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="PKR", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_transactions_idempotency_key"),
        Index("ix_transactions_created_status", "created_at", "status"),
        CheckConstraint("amount > 0", name="ck_transaction_amount_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    sender_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.id"), index=True)
    receiver_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="PKR", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), default="TRANSFER", nullable=False)
    channel: Mapped[str] = mapped_column(String(40), default="WALLET_APP", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("ix_ledger_wallet_created", "wallet_id", "created_at"),
        CheckConstraint("amount > 0", name="ck_ledger_amount_positive"),
        CheckConstraint("entry_type IN ('DEBIT', 'CREDIT')", name="ck_ledger_entry_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"), index=True, nullable=False)
    wallet_id: Mapped[str] = mapped_column(ForeignKey("wallets.id"), index=True, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"), unique=True, index=True, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False)
    reasons_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    alert_id: Mapped[str] = mapped_column(ForeignKey("fraud_alerts.id"), index=True, nullable=False)
    analyst_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_list_json: Mapped[list] = mapped_column(JSON, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.70"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(150), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ApiCall(Base):
    __tablename__ = "api_calls"
    __table_args__ = (Index("ix_api_calls_created_endpoint", "created_at", "endpoint"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    consent_id: Mapped[str | None] = mapped_column(ForeignKey("consents.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CbdcWallet(Base):
    __tablename__ = "cbdc_wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True)
    owner_label: Mapped[str] = mapped_column(String(180), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="ePKR", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CbdcOperation(Base):
    __tablename__ = "cbdc_operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    reference: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    source_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("cbdc_wallets.id"))
    destination_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("cbdc_wallets.id"))
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_created_entity", "created_at", "entity_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    correlation_id: Mapped[str | None] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
