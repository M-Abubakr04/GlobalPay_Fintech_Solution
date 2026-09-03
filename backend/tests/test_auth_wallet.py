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
