# API Testing Guide

## Swagger UI

Open `http://localhost:8000/docs`.

1. Execute `POST /api/v1/auth/login`.
2. Copy the access token.
3. Select **Authorize** and enter the bearer token.
4. Execute wallet, payment, fraud, Open Banking and dashboard routes.

## Postman

Import:

- `postman/GlobalPay.postman_collection.json`
- `postman/GlobalPay.local.postman_environment.json`

Run the login request first. Its test script stores the token in the active environment.

## Automated tests

```bash
docker compose exec backend pytest -q --cov=app
```

## Evidence

Export the Postman run and save it under `docs/reports/`.
