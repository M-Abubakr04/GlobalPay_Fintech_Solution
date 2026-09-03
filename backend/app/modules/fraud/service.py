from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import FRAUD_ALERTS
from app.models.entities import FraudAlert, ModelRegistry, Transaction

FEATURES = ["amount", "hour", "velocity_1h", "new_device", "merchant_risk"]


def _rule_score(
    *,
    amount: float,
    hour: int,
    velocity_1h: int,
    new_device: int,
    merchant_risk: float,
    average_amount: float,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    amount_ratio = amount / max(average_amount, 1.0)
    unusual_amount = min(max((amount_ratio - 1.5) / 5.0, 0), 1)
    if amount_ratio >= 4:
        reasons.append("Amount is significantly higher than the wallet's normal history")
    night = 1.0 if hour in {0, 1, 2, 3, 4} else 0.0
    if night:
        reasons.append("Transaction occurred during an unusual night-time window")
    velocity = min(velocity_1h / 6.0, 1.0)
    if velocity_1h >= 4:
        reasons.append("High transaction velocity within one hour")
    if new_device:
        reasons.append("New device indicator")
    if merchant_risk >= 0.7:
        reasons.append("High merchant risk indicator")

    score = (
        0.40 * unusual_amount
        + 0.18 * night
        + 0.20 * velocity
        + 0.12 * float(new_device)
        + 0.10 * merchant_risk
    )
    return min(max(score, 0.01), 0.99), reasons


def score_payment(
    db: Session,
    *,
    sender_wallet_id: str,
    amount: Decimal,
    merchant_risk: float = 0.1,
    new_device: int = 0,
    event_time: datetime | None = None,
) -> dict[str, Any]:
    event_time = event_time or datetime.now(UTC)
    since = event_time - timedelta(hours=1)
    velocity = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.sender_wallet_id == sender_wallet_id,
            Transaction.created_at >= since,
        )
    ) or 0
    average = db.scalar(
        select(func.avg(Transaction.amount)).where(
            Transaction.sender_wallet_id == sender_wallet_id,
            Transaction.status == "COMPLETED",
        )
    ) or Decimal("10000")

    features = {
        "amount": float(amount),
        "hour": event_time.hour,
        "velocity_1h": int(velocity),
        "new_device": int(new_device),
        "merchant_risk": float(merchant_risk),
    }

    model_path = settings.model_path
    if model_path.exists():
        artifact = joblib.load(model_path)
        model = artifact["model"]
        probability = float(model.predict_proba(pd.DataFrame([features])[FEATURES])[:, 1][0])
        _, reasons = _rule_score(average_amount=float(average), **features)
    else:
        probability, reasons = _rule_score(average_amount=float(average), **features)

    band = "HIGH" if probability >= 0.70 else "MEDIUM" if probability >= 0.40 else "LOW"
    return {
        "score": round(probability, 4),
        "confidence": round(max(probability, 1 - probability), 4),
        "risk_band": band,
        "reasons": reasons or ["No major anomaly signal detected"],
        "features": features,
    }


def create_alert_if_needed(db: Session, transaction: Transaction, result: dict[str, Any]) -> FraudAlert | None:
    if result["score"] < 0.40:
        return None
    alert = FraudAlert(
        transaction_id=transaction.id,
        risk_score=Decimal(str(result["score"])),
        confidence=Decimal(str(result["confidence"])),
        risk_band=result["risk_band"],
        reasons_json=result["reasons"],
        status="OPEN",
    )
    db.add(alert)
    FRAUD_ALERTS.labels(risk_band=result["risk_band"]).inc()
    return alert


def train_model(db: Session, dataset_path: str | None = None) -> ModelRegistry:
    source = Path(dataset_path or settings.fraud_dataset_path)
    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")

    df = pd.read_csv(source)
    missing = set(FEATURES + ["is_fraud"]) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {sorted(missing)}")

    x = df[FEATURES]
    y = df["is_fraud"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ]
    )
    model.fit(x_train, y_train)
    prediction = model.predict(x_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, prediction)), 4),
        "precision": round(float(precision_score(y_test, prediction, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, prediction, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, prediction, zero_division=0)), 4),
        "rows": int(len(df)),
        "fraud_rate": round(float(y.mean()), 4),
    }

    settings.model_path.parent.mkdir(parents=True, exist_ok=True)
    version = datetime.now(UTC).strftime("fraud-%Y%m%d-%H%M%S")
    joblib.dump(
        {"model": model, "features": FEATURES, "metrics": metrics, "version": version},
        settings.model_path,
    )

    for registry in db.scalars(select(ModelRegistry).where(ModelRegistry.is_active.is_(True))):
        registry.is_active = False
    registry = ModelRegistry(
        version=version,
        algorithm="StandardScaler + LogisticRegression",
        feature_list_json=FEATURES,
        metrics_json=metrics,
        threshold=Decimal("0.7000"),
        is_active=True,
    )
    db.add(registry)
    db.flush()
    return registry
