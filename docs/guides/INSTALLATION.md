# Installation Guide

## Prerequisites

- Ubuntu 22.04 or later
- Docker Engine
- Docker Compose plugin
- Git
- At least 8 GB RAM; 16 GB recommended

## Install and start

```bash
git clone <your-repository-url>
cd Global_Pay_FinTech_Solutions
python3 scripts/generate_env.py
docker compose up --build -d
docker compose ps
```

Wait until all services show `healthy` or `running`.

## URLs

- React application: `http://localhost:3000`
- FastAPI Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

The generated Grafana password is stored in `.env`.

## Stop

```bash
docker compose down
```

Preserve data by avoiding `-v`. To remove all demo data:

```bash
docker compose down -v
```
