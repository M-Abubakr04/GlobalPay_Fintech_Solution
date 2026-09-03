from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter("globalpay_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("globalpay_http_request_duration_seconds", "HTTP request latency", ["method", "path"])
PAYMENTS = Counter("globalpay_payments_total", "Simulated payment outcomes", ["status", "payment_type"])
FRAUD_ALERTS = Counter("globalpay_fraud_alerts_total", "Fraud alerts created", ["risk_band"])
OPEN_BANKING_CALLS = Counter(
    "globalpay_open_banking_calls_total",
    "Open Banking and CBDC API calls",
    ["endpoint", "status"],
)
