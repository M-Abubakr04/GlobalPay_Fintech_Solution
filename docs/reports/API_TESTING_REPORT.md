# API Testing Report

## Tools

- FastAPI OpenAPI schema: `http://localhost:8000/openapi.json`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Postman collection: `postman/GlobalPay.postman_collection.json`
- Postman environment: `postman/GlobalPay.local.postman_environment.json`

## Purpose

Swagger/ReDoc provide API documentation generated from the FastAPI application. Postman provides a repeatable manual API testing flow for the main demonstration paths.

## Covered Postman scenarios

- Platform health check
- Customer login
- Authenticated profile check
- Customer wallet overview
- Wallet activity
- Wallet transfer
- Transaction history
- Open Banking consent creation
- AIS account information request
- CBDC wallet creation/operation flow
- Executive/management style API checks where included in the collection

## Execution command

After starting Docker Compose, the collection can be executed manually in Postman or with Newman:

```bash
newman run postman/GlobalPay.postman_collection.json \
  -e postman/GlobalPay.local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export docs/reports/newman-api-test-results.json
```

## Evidence statement

The collection is included as source evidence. If a JSON execution export is produced, it must correspond to the current collection version before submission.

## Verified live check

On 3 September 2026, the live smoke flow passed against the Docker Compose deployment: liveness,
database/Redis readiness, authentication, and authenticated wallet retrieval all returned successful
responses. The executive and financial reporting endpoints were also authenticated and returned a
read-only dashboard, seven-day trend data, PKR currency, and a populated financial breakdown.
