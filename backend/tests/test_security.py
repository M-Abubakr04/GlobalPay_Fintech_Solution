from app.core.security import decrypt_pii, encrypt_pii, hash_password, verify_password


def test_password_hash_is_not_plain_text():
    digest = hash_password("StrongPass123!")
    assert digest != "StrongPass123!"
    assert verify_password("StrongPass123!", digest)


def test_pii_round_trip():
    encrypted = encrypt_pii("35202-1234567-8")
    assert encrypted != "35202-1234567-8"
    assert decrypt_pii(encrypted) == "35202-1234567-8"
