from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import Merchant, Transaction, User, Wallet


def test_registration_creates_wallet(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.customer@example.com",
            "password": "StrongPass123!",
            "full_name": "New Customer",
            "phone": "03001234567",
            "national_id": "35202-0000000-0",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["wallet_id"]
    assert "wallet created" in payload["message"].lower()


def test_login_and_wallet(client):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "new.customer@example.com", "password": "StrongPass123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/wallets/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["currency"] == "PKR"


def test_merchant_can_view_settlement_report(client):
    db = SessionLocal()
    merchant_user = User(
        email="portal.merchant@example.com",
        password_hash=hash_password("MerchantPass123!"),
        role="merchant",
    )
    db.add(merchant_user)
    db.flush()
    merchant = Merchant(
        user_id=merchant_user.id,
        business_name="Portal Test Store",
        status="APPROVED",
        settlement_config={"cycle": "T+1"},
    )
    db.add(merchant)
    db.flush()
    wallet = Wallet(merchant_id=merchant.id, balance=Decimal("1250.00"), currency="PKR")
    db.add(wallet)
    db.flush()
    db.add(
        Transaction(
            reference="GP-MERCHANT-PORTAL-TEST",
            receiver_wallet_id=wallet.id,
            amount=Decimal("1250.00"),
            currency="PKR",
            transaction_type="MERCHANT_PAYMENT",
            channel="MERCHANT_PORTAL",
            status="COMPLETED",
            description="Merchant portal test payment",
            idempotency_key="merchant-portal-test-payment",
        )
    )
    db.commit()
    db.close()

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "portal.merchant@example.com", "password": "MerchantPass123!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/customers/merchant/me/report",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["business_name"] == "Portal Test Store"
    assert payload["settlement_cycle"] == "T+1"
    assert payload["completed_payment_count"] == 1
    assert payload["completed_payment_volume"] == "1250.00"
    assert payload["payments"][0]["reference"] == "GP-MERCHANT-PORTAL-TEST"
