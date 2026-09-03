import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings
from app.core.metrics import HTTP_LATENCY, HTTP_REQUESTS
from app.core.rate_limit import allow_request
from app.modules.auth.router import router as auth_router
from app.modules.cbdc.router import router as cbdc_router
from app.modules.customers.router import router as customers_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.fraud.router import router as fraud_router
from app.modules.health.router import router as health_router
from app.modules.open_banking.router import router as open_banking_router
from app.modules.payments.router import router as payments_router
from app.modules.wallets.router import router as wallets_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("globalpay")

app = FastAPI(
    title="GlobalPay FinTech Solutions API",
    description=(
        "Standards-aligned modular-monolith proof of concept for digital wallets, "
        "simulated payments, AI-assisted fraud review, Open Banking/CBDC simulation "
        "and executive reporting. No real banking or cardholder data is processed."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_and_metrics(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    status_code = 500

    client_identity = request.client.host if request.client else "unknown"
    allowed, limit = allow_request(client_identity, request.url.path)
    if not allowed:
        response = JSONResponse(
            status_code=429,
            content={
                "detail": "Request rate limit exceeded",
                "correlation_id": correlation_id,
            },
            headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)},
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        logger.exception(
            "Unhandled request error",
            extra={"correlation_id": correlation_id, "path": request.url.path},
        )
        response = JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id,
            },
        )
    elapsed = time.perf_counter() - started
    path_template = request.scope.get("route")
    metric_path = getattr(path_template, "path", request.url.path)
    HTTP_REQUESTS.labels(
        method=request.method,
        path=metric_path,
        status=str(status_code),
    ).inc()
    HTTP_LATENCY.labels(method=request.method, path=metric_path).observe(elapsed)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/", tags=["Platform"])
def root():
    return {
        "name": settings.app_name,
        "architecture": "modular monolith",
        "modules": [
            "customer-wallet",
            "payments",
            "fraud-ai",
            "open-banking-cbdc",
            "executive-dashboard",
        ],
        "swagger": "/docs",
        "health": "/health/ready",
        "simulation_only": True,
    }


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(customers_router, prefix=settings.api_v1_prefix)
app.include_router(wallets_router, prefix=settings.api_v1_prefix)
app.include_router(payments_router, prefix=settings.api_v1_prefix)
app.include_router(fraud_router, prefix=settings.api_v1_prefix)
app.include_router(open_banking_router, prefix=settings.api_v1_prefix)
app.include_router(cbdc_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
