from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.audit import record_audit
from app.core.database import get_db
from app.models.entities import FraudAlert, Investigation, ModelRegistry, Transaction, User
from app.modules.fraud.schemas import AlertOut, ManualScoreRequest, ReviewRequest
from app.modules.fraud.service import score_payment, train_model

router = APIRouter(prefix="/fraud", tags=["Module 3 - Fraud AI"])


@router.post("/score")
def manual_score(
    payload: ManualScoreRequest,
    _: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
):
    return score_payment(
        db,
        sender_wallet_id=payload.sender_wallet_id,
        amount=payload.amount,
        merchant_risk=payload.merchant_risk,
        new_device=int(payload.new_device),
    )


@router.post("/train")
def train(
    request: Request,
    user: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
):
    try:
        registry = train_model(db)
        record_audit(
            db,
            action="FRAUD_MODEL_TRAINED",
            entity_type="model_registry",
            entity_id=registry.id,
            actor_user_id=user.id,
            correlation_id=getattr(request.state, "correlation_id", None),
            metadata={"version": registry.version, "metrics": registry.metrics_json},
        )
        db.commit()
        return {
            "model_id": registry.id,
            "version": registry.version,
            "algorithm": registry.algorithm,
            "features": registry.feature_list_json,
            "metrics": registry.metrics_json,
            "human_review_required": True,
        }
    except (FileNotFoundError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status_filter: str | None = None,
    _: User = Depends(require_roles("admin", "analyst", "executive")),
    db: Session = Depends(get_db),
):
    query = select(FraudAlert, Transaction).join(Transaction, Transaction.id == FraudAlert.transaction_id)
    if status_filter:
        query = query.where(FraudAlert.status == status_filter)
    rows = db.execute(query.order_by(FraudAlert.created_at.desc()).limit(200)).all()
    return [
        AlertOut(
            id=alert.id,
            transaction_id=alert.transaction_id,
            transaction_reference=txn.reference,
            risk_score=alert.risk_score,
            confidence=alert.confidence,
            risk_band=alert.risk_band,
            status=alert.status,
            reasons=alert.reasons_json,
            created_at=alert.created_at,
        )
        for alert, txn in rows
    ]


@router.post("/alerts/{alert_id}/review")
def review_alert(
    alert_id: str,
    payload: ReviewRequest,
    request: Request,
    analyst: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
):
    alert = db.get(FraudAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    investigation = Investigation(
        alert_id=alert.id,
        analyst_user_id=analyst.id,
        decision=payload.decision,
        notes=payload.notes,
    )
    alert.status = "CLOSED" if payload.decision in {"CONFIRMED_FRAUD", "LEGITIMATE"} else "ESCALATED"
    db.add(investigation)
    record_audit(
        db,
        action="FRAUD_ALERT_REVIEWED",
        entity_type="fraud_alert",
        entity_id=alert.id,
        actor_user_id=analyst.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        metadata={"decision": payload.decision},
    )
    db.commit()
    return {"alert_id": alert.id, "status": alert.status, "decision": payload.decision}


@router.get("/investigations/{alert_id}")
def investigation_history(
    alert_id: str,
    _: User = Depends(require_roles("admin", "analyst", "executive")),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(Investigation)
            .where(Investigation.alert_id == alert_id)
            .order_by(Investigation.created_at.desc())
        )
    )


@router.get("/model/latest")
def latest_model(
    _: User = Depends(require_roles("admin", "analyst", "executive")),
    db: Session = Depends(get_db),
):
    model = db.scalar(
        select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).order_by(ModelRegistry.trained_at.desc())
    )
    if not model:
        return {"status": "NOT_TRAINED", "message": "Use POST /fraud/train to train the demo classifier"}
    return {
        "version": model.version,
        "algorithm": model.algorithm,
        "features": model.feature_list_json,
        "metrics": model.metrics_json,
        "threshold": model.threshold,
        "trained_at": model.trained_at,
        "human_review_required": True,
    }
