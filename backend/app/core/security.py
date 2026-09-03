import base64
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

# Argon2id is purpose-built for password hashing. The parameters are encoded into
# each hash, allowing future upgrades without storing plaintext passwords.
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_digest: str) -> bool:
    try:
        return password_hasher.verify(password_digest, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    expiry = now + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "jti": base64.urlsafe_b64encode(os.urandom(12)).decode(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def _aesgcm() -> AESGCM:
    raw_key = base64.urlsafe_b64decode(settings.pii_encryption_key.encode())
    if len(raw_key) != 32:
        raise ValueError("PII_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return AESGCM(raw_key)


def encrypt_pii(value: str | None) -> str | None:
    if not value:
        return None
    nonce = os.urandom(12)
    ciphertext = _aesgcm().encrypt(nonce, value.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_pii(value: str | None) -> str | None:
    if not value:
        return None
    raw = base64.urlsafe_b64decode(value.encode())
    nonce, ciphertext = raw[:12], raw[12:]
    return _aesgcm().decrypt(nonce, ciphertext, None).decode()
