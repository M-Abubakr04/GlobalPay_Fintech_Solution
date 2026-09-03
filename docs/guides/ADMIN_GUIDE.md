# Administrator Guide

## Health and logs

```bash
docker compose ps
curl http://localhost:8000/health/ready
docker compose logs --tail=200 backend
```

## Database access

```bash
docker compose exec postgres psql -U globalpay -d globalpay
```

Useful queries:

```sql
SELECT reference, amount, status, risk_score, created_at
FROM transactions ORDER BY created_at DESC LIMIT 20;

SELECT risk_band, status, count(*)
FROM fraud_alerts GROUP BY risk_band, status;

SELECT action, entity_type, correlation_id, created_at
FROM audit_logs ORDER BY created_at DESC LIMIT 20;
```

## Reseed demo data

```bash
docker compose exec backend python -m app.seed
```

The seed is idempotent and does not duplicate the primary demo users.

## Backup and restore

Use `scripts/backup_database.sh`. Test restoration in a separate environment before relying on a backup.
