# Deployment Guide

## Local assessment deployment

The supported assessment deployment is Docker Compose.

```bash
python3 scripts/generate_env.py
docker compose up --build -d
docker compose ps
docker compose logs -f backend
```

## Container topology

- `frontend`: Nginx-hosted React production build
- `backend`: FastAPI modular monolith
- `postgres`: authoritative relational data and financial ledger
- `redis`: non-authoritative cache and idempotency acceleration
- `prometheus`: metrics collection
- `grafana`: provisioned operations dashboard

All services communicate on the private `globalpay-net` bridge network. Only presentation/demo ports are published.

## Verification

```bash
bash scripts/demo_smoke_test.sh
docker compose exec backend pytest -q
curl http://localhost:8000/metrics
```

## Backup

```bash
bash scripts/backup_database.sh
```

## Production differences

A real production deployment would require managed secrets, TLS certificates, WAF/load balancing, PostgreSQL high availability, encrypted volumes, centralised logs, backup testing and formal compliance assessment.
