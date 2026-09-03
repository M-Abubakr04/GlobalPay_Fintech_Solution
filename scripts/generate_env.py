from base64 import urlsafe_b64encode
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"

if target.exists():
    print(f"{target} already exists. Delete it first if you want new secrets.")
    raise SystemExit(0)

db_password = secrets.token_urlsafe(20)
jwt_secret = secrets.token_urlsafe(48)
pii_key = urlsafe_b64encode(secrets.token_bytes(32)).decode()
grafana_password = secrets.token_urlsafe(16)

target.write_text(
    f"""APP_NAME=GlobalPay FinTech Solutions
ENVIRONMENT=development
DEBUG=true

FRONTEND_PORT=3000
BACKEND_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

POSTGRES_DB=globalpay
POSTGRES_USER=globalpay
POSTGRES_PASSWORD={db_password}
DATABASE_URL=postgresql+psycopg://globalpay:{db_password}@postgres:5432/globalpay
REDIS_URL=redis://redis:6379/0

JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
PII_ENCRYPTION_KEY={pii_key}

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD={grafana_password}

VITE_API_BASE_URL=/api/v1
""",
    encoding="utf-8",
)
print(f"Created {target} with fresh local-development secrets.")
print("Keep .env out of Git; .gitignore already excludes it.")
