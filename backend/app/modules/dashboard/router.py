from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.cache import cache_get_json, cache_set_json
from app.core.database import get_db
from app.models.entities import (
    ApiCall,
    CbdcOperation,
    CbdcWallet,
    Customer,
    FraudAlert,
    Merchant,
    Transaction,
    User,
    Wallet,
)

router = APIRouter(prefix="/dashboard", tags=["Module 5 - Executive Dashboard"])


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _build_trends(db: Session, days: int = 7) -> list[dict]:
    start = datetime.now(UTC) - timedelta(days=days - 1)
    rows = db.execute(
        select(Transaction.created_at, Transaction.amount)
        .where(Transaction.created_at >= start, Transaction.status == "COMPLETED")
        .order_by(Transaction.created_at)
    ).all()
    by_day: dict[str, dict] = {}
    for created_at, amount in rows:
        day = created_at.date().isoformat()
        current = by_day.setdefault(day, {"payments": 0, "volume": Decimal("0.00")})
        current["payments"] += 1
        current["volume"] += _decimal(amount)

    output = []
    for offset in range(days):
        day = (date.today() - timedelta(days=days - 1 - offset)).isoformat()
        data = by_day.get(day, {"payments": 0, "volume": Decimal("0.00")})
        output.append(
            {
                "date": day,
                "payments": data["payments"],
                "volume": str(_decimal(data["volume"])),
            }
        )
    return output


@router.get("/executive")
def executive_dashboard(
    _: User = Depends(require_roles("admin", "executive", "analyst")),
    db: Session = Depends(get_db),
):
    cached = cache_get_json("dashboard:executive")
    if cached:
        return cached

    active_customers = db.scalar(
        select(func.count(Customer.id)).where(Customer.is_active.is_(True))
    ) or 0
    digital_wallets = db.scalar(select(func.count(Wallet.id))) or 0
    active_merchants = db.scalar(
        select(func.count(Merchant.id)).where(Merchant.status.in_(["ACTIVE", "APPROVED"]))
    ) or 0
    payment_count = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.status == "COMPLETED")
    ) or 0
    total_transactions = db.scalar(select(func.count(Transaction.id))) or 0
    payment_volume = _decimal(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.status == "COMPLETED")
        )
    )
    open_fraud_alerts = db.scalar(
        select(func.count(FraudAlert.id)).where(FraudAlert.status == "OPEN")
    ) or 0
    high_risk_alerts = db.scalar(
        select(func.count(FraudAlert.id)).where(FraudAlert.risk_band == "HIGH")
    ) or 0
    api_calls = db.scalar(select(func.count(ApiCall.id))) or 0
    cbdc_wallets = db.scalar(select(func.count(CbdcWallet.id))) or 0
    cbdc_volume = _decimal(
        db.scalar(
            select(func.coalesce(func.sum(CbdcOperation.amount), 0))
            .where(CbdcOperation.operation_type == "TRANSFER")
        )
    )

    payload = {
        "active_customers": int(active_customers),
        "digital_wallets": int(digital_wallets),
        "active_merchants": int(active_merchants),
        "payment_count": int(payment_count),
        "payment_volume": str(payment_volume),
        "open_fraud_alerts": int(open_fraud_alerts),
        "high_risk_alerts": int(high_risk_alerts),
        "api_calls": int(api_calls),
        "cbdc_wallets": int(cbdc_wallets),
        "cbdc_volume": str(cbdc_volume),
        "payment_success_rate": round(
            (payment_count / total_transactions * 100), 2
        ) if total_transactions else 100.0,
        "trends": _build_trends(db),
        "read_only": True,
        "standards_alignment": [
            "COBIT 2019 governance and KPI accountability",
            "NIST CSF risk visibility",
            "ISO 27001 least privilege and auditability",
            "ISO 27018 PII minimisation in reports",
        ],
    }
    cache_set_json("dashboard:executive", payload, ttl_seconds=30)
    return payload


@router.get("/operations")
def operations_dashboard(
    _: User = Depends(require_roles("admin", "executive", "analyst")),
    db: Session = Depends(get_db),
):
    latest_transactions = list(
        db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(10))
    )
    latest_alerts = list(
        db.scalars(select(FraudAlert).order_by(FraudAlert.created_at.desc()).limit(10))
    )
    return {
        "latest_transactions": latest_transactions,
        "latest_alerts": latest_alerts,
        "read_only": True,
    }
