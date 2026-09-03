from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Platform Health"])


@router.get("/live")
def liveness():
    return {"status": "alive", "service": "globalpay-backend"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    checks = {"database": "down", "redis": "down"}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"checks": checks, "error": str(exc)}) from exc

    try:
        if redis_client.ping():
            checks["redis"] = "up"
    except Exception:
        # Redis is a cache and must not become the source of truth; readiness reports degradation.
        checks["redis"] = "degraded"

    return {
        "status": "ready" if checks["database"] == "up" else "not-ready",
        "checks": checks,
    }
