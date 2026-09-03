from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import User, Wallet


def _register(client, email: str, name: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": name,
            "phone": "03001234567",
            "national_id": "SIMULATED-ID",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_connected_module_flow(client):
    sender = _register(client, "flow.sender@example.com", "Flow Sender")
    _register(client, "flow.receiver@example.com", "Flow Receiver")

    db = SessionLocal()
    wallet = db.get(Wallet, sender["wallet_id"])
    wallet.balance = Decimal("900000.00")
    analyst = User(
        email="flow.analyst@example.com",
        password_hash=hash_password("AnalystPass123!"),
        role="analyst",
    )
    executive = User(
        email="flow.executive@example.com",
        password_hash=hash_password("ExecutivePass123!"),
        role="executive",
    )
    db.add_all([analyst, executive])
    db.commit()
    db.close()

    customer_token = _login(client, "flow.sender@example.com", "StrongPass123!")
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    transfer = client.post(
        "/api/v1/payments/transfer",
        headers={**customer_headers, "Idempotency-Key": "connected-flow-1"},
        json={
            "receiver_email": "flow.receiver@example.com",
            "amount": "450000.00",
            "description": "Connected-module integration test",
            "new_device": True,
        },
    )
    assert transfer.status_code == 200, transfer.text
    transaction = transfer.json()
    assert transaction["status"] == "COMPLETED"

    duplicate = client.post(
        "/api/v1/payments/transfer",
        headers={**customer_headers, "Idempotency-Key": "connected-flow-1"},
        json={
            "receiver_email": "flow.receiver@example.com",
            "amount": "450000.00",
            "description": "Connected-module integration test",
            "new_device": True,
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == transaction["id"]

    consent = client.post(
        "/api/v1/open-banking/consents",
        headers=customer_headers,
        json={
            "client_name": "Integration Budget App",
            "scopes": ["accounts:read", "payments:write"],
            "expires_in_hours": 24,
        },
    )
    assert consent.status_code == 200, consent.text

    ais = client.get(
        f"/api/v1/open-banking/ais/accounts/{sender['wallet_id']}",
        headers=customer_headers,
        params={"consent_id": consent.json()["id"]},
    )
    assert ais.status_code == 200, ais.text
    assert ais.json()["account_id"] == sender["wallet_id"]

    analyst_token = _login(client, "flow.analyst@example.com", "AnalystPass123!")
    train = client.post(
        "/api/v1/fraud/train",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert train.status_code == 200, train.text
    assert train.json()["human_review_required"] is True

    executive_token = _login(client, "flow.executive@example.com", "ExecutivePass123!")
    dashboard = client.get(
        "/api/v1/dashboard/executive",
        headers={"Authorization": f"Bearer {executive_token}"},
    )
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["payment_count"] >= 1
    assert dashboard.json()["read_only"] is True

    financial_report = client.get(
        "/api/v1/payments/reports/financial",
        headers={"Authorization": f"Bearer {executive_token}"},
    )
    assert financial_report.status_code == 200, financial_report.text
    assert financial_report.json()["currency"] == "PKR"
    assert financial_report.json()["breakdown"]
