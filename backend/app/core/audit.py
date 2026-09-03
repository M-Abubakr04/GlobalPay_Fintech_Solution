from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def record_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    actor_user_id: str | None,
    correlation_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    # ISO 27001/COBIT alignment: accountability without storing raw customer PII.
    db.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            metadata_json=metadata or {},
        )
    )
