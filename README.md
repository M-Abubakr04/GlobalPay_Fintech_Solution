# GlobalPay FinTech Solutions

GlobalPay is a laptop-optimised, standards-aligned **modular monolith** proof of concept for an enterprise FinTech platform.

It implements five connected functional modules:

1. Customer and Digital Wallet Management
2. Digital Payment Processing
3. AI-Assisted Fraud Detection
4. Open Banking and CBDC Simulation
5. Executive Financial Operations Dashboard

## Project objectives

- Integrate disconnected wallet, payment, fraud, Open Banking/CBDC and reporting capabilities into one platform.
- Demonstrate secure customer onboarding, simulated wallet operations and payment processing.
- Provide AI-assisted fraud-risk scoring with human review and investigation history.
- Provide management visibility through read-only executive KPIs and operational reporting.
- Keep the implementation suitable for a standard student laptop using Docker Compose.

## Architecture

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI modular monolith
- **Database:** PostgreSQL
- **Cache:** Redis for temporary cache/rate-limit/idempotency support only
- **AI:** Scikit-learn, Pandas, NumPy
- **Observability:** Prometheus + Grafana
- **Deployment:** Docker Compose
- **API documentation:** OpenAPI with Swagger UI and ReDoc
- **API testing:** Postman collection and automated Pytest coverage

The five business modules are separated in code by routers, schemas, services and tests, but run in a single FastAPI deployment unit. This avoids distributed-transaction complexity while preserving future microservice extraction boundaries.

## Quick start

```bash
cd Global_Pay_FinTech_Solutions
python3 scripts/generate_env.py
docker compose up --build -d
docker compose ps
```

Open:

- Application: http://localhost:3000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

The host ports are configurable in `.env` through `FRONTEND_PORT`, `BACKEND_PORT`,
`PROMETHEUS_PORT`, and `GRAFANA_PORT`. Container-to-container ports stay fixed, so the
internal proxy, health checks, and monitoring continue to work. For example:

```dotenv
FRONTEND_PORT=3100
BACKEND_PORT=8100
PROMETHEUS_PORT=9190
GRAFANA_PORT=3101
```

With those values, open the application at `http://localhost:3100`. The frontend uses
the same-origin `/api/v1` proxy, so changing the backend host port does not break it.

Grafana default local credentials are controlled by `.env`; the generated defaults are normally `admin / admin` unless changed.

## Demo users

| Role | Email | Password |
|---|---|---|
| Customer | customer@globalpay.example.com | Customer123! |
| Customer 2 | receiver@globalpay.example.com | Receiver123! |
| Merchant | merchant@globalpay.example.com | Merchant123! |
| Fraud analyst | analyst@globalpay.example.com | Analyst123! |
| Executive | executive@globalpay.example.com | Executive123! |
| Administrator | admin@globalpay.example.com | Admin123! |

These credentials are strictly for a local demonstration.

## Demonstration path

1. Start the platform with Docker Compose.
2. Open the React frontend and log in as the customer.
3. View wallet balance and wallet activity.
4. Transfer funds to `receiver@globalpay.example.com`.
5. Open transaction history and verify the status/reference.
6. Log in as the analyst and review fraud alerts/investigations.
7. Open the Open Banking/CBDC page and demonstrate consent/API/CBDC activity.
8. Log in as the executive and view cross-module KPIs.
9. Open Reports and export the financial CSV and executive JSON evidence.
10. Open Swagger/ReDoc for API documentation.
11. Open Prometheus/Grafana to show API metrics and health.

## Testing methodology

- **Automated backend tests:** `pytest` validates authentication, wallet creation, security controls and connected module flows.
- **Frontend build validation:** `npm run build` verifies the React/Vite project builds successfully.
- **API documentation/testing:** Swagger UI and ReDoc are generated from FastAPI OpenAPI; Postman provides a repeatable manual API flow.
- **Security checks:** `scripts/run_security_scans.sh` supports Semgrep and Trivy evidence where installed.
- **Smoke testing:** `scripts/demo_smoke_test.sh` validates the main demo endpoints quickly after startup.

Validation commands:

```bash
PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm install && npm run build
```

## Assumptions and limitations

- All transactions and datasets are simulated.
- No real banking, card network, central-bank system or customer financial data is connected.
- PCI DSS, ISO 27017 and other formal frameworks are treated as conceptual alignment/control mapping, not certification.
- Docker Compose is used for laptop-scale demonstration; the system is not a high-availability production deployment.
- Redis is not an authoritative financial data store; PostgreSQL remains the source of truth.
- The AI model is lightweight and suitable for proof-of-concept demonstration, not production fraud detection.

## Future enhancements

- Cloud deployment with private networking and managed PostgreSQL/Redis.
- Enterprise identity provider integration using OIDC.
- Real Open Banking sandbox integration.
- Event-driven processing for higher transaction throughput.
- Formal compliance assessment path for PCI DSS, ISO 27001 and production governance.
- Optional K3s/Kind deployment if orchestration becomes part of a future requirement.

## Repository structure

```text
Global_Pay_FinTech_Solutions/
├── .github/workflows/          GitHub Actions CI
├── backend/                    FastAPI modular monolith
│   ├── app/core/               configuration, security, cache, metrics
│   ├── app/models/             PostgreSQL entities
│   └── app/modules/            functional modules and routers
├── frontend/                   React/Vite role-based portals
├── datasets/                   synthetic fraud dataset
├── database/                   PostgreSQL schema reference
├── monitoring/                 Prometheus and Grafana provisioning
├── postman/                    Postman collection and local environment
├── docs/                       architecture, guides and evidence reports
├── k8s/                        optional K3s/Kind manifests
├── scripts/                    environment, scans, backup and smoke test
├── compose.yaml                complete local deployment
├── .env.example                safe environment template
└── README.md                   project overview and operating guide
```

## Important scope statement

This is a simulated educational platform. It does not connect to real banks, card networks, central-bank systems, or real customer financial data. Framework references describe implementation alignment and control mapping, not formal certification.
