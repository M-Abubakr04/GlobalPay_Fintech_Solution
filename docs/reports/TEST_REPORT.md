# Test Report

**Verification date:** 3 September 2026
**Environment:** Docker Engine, Python 3.12 backend image, Node.js 22 frontend build

## Verified results

| Check | Command / scope | Result |
|---|---|---|
| Backend automated tests | Pytest in the built backend image | **5 passed**, 1 upstream deprecation warning |
| Frontend production build | `npm run build` | **Passed**, 2,271 modules transformed |
| Docker Compose configuration | `docker compose config --quiet` | **Passed** |
| Full stack startup | PostgreSQL, Redis, FastAPI, React/Nginx, Prometheus, Grafana | **Started successfully** |
| Backend readiness | `GET /health/ready` | **Database up, Redis up** |
| Frontend-to-backend proxy | `GET /health/ready` through port 3000 | **Passed** |
| Authenticated smoke test | Login and `GET /api/v1/wallets/me` | **Passed** |

## Automated coverage

- Customer registration and automatic wallet creation.
- Duplicate-email rejection and login/token handling.
- Authentication requirements for protected wallet APIs.
- Connected transfer with idempotent replay.
- Open Banking consent and account-information flow.
- Lightweight fraud-model training with mandatory human review.
- Executive dashboard aggregation and read-only flag.
- Financial report response, currency, and populated breakdown.
- Encryption round trip, password hashing, and role-based route denial.

## Notes

The frontend build reports a non-blocking bundle-size warning. The automated suite reports one
Starlette/httpx deprecation warning from an upstream test-client compatibility layer. Neither warning
caused a functional failure. All financial records are simulated; these results are proof-of-concept
verification and not production certification.
