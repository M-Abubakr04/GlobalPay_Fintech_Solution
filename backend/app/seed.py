from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import encrypt_pii, hash_password
from app.models.entities import (
    CbdcOperation,
    CbdcWallet,
    Consent,
    Customer,
    Merchant,
    User,
    Wallet,
)

DEMO_USERS = [
    ("customer@globalpay.example.com", "Customer123!", "customer", "Ayesha Khan"),
    ("receiver@globalpay.example.com", "Receiver123!", "customer", "Bilal Ahmed"),
    ("merchant@globalpay.example.com", "Merchant123!", "merchant", "GlobalMart Merchant"),
    ("analyst@globalpay.example.com", "Analyst123!", "analyst", None),
    ("executive@globalpay.example.com", "Executive123!", "executive", None),
    ("admin@globalpay.example.com", "Admin123!", "admin", None),
]


def create_user(db, email: str, password: str, role: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed():
    db = SessionLocal()
    try:
        created = {}
        for email, password, role, _full_name in DEMO_USERS:
            created[email] = create_user(db, email, password, role)

        customer_specs = [
            ("customer@globalpay.example.com", "Ayesha Khan", "03001234567", "35202-1234567-8", Decimal("150000.00")),
            ("receiver@globalpay.example.com", "Bilal Ahmed", "03111234567", "35202-7654321-0", Decimal("25000.00")),
        ]
        for email, full_name, phone, national_id, opening_balance in customer_specs:
            user = created[email]
            customer = db.scalar(select(Customer).where(Customer.user_id == user.id))
            if not customer:
                customer = Customer(
                    user_id=user.id,
                    full_name=full_name,
                    phone_encrypted=encrypt_pii(phone),
                    national_id_encrypted=encrypt_pii(national_id),
                    kyc_status="VERIFIED",
                )
                db.add(customer)
                db.flush()
            wallet = db.scalar(select(Wallet).where(Wallet.customer_id == customer.id))
            if not wallet:
                wallet = Wallet(
                    customer_id=customer.id,
                    balance=opening_balance,
                    currency="PKR",
                    status="ACTIVE",
                )
                db.add(wallet)
                db.flush()

            consent = db.scalar(
                select(Consent).where(
                    Consent.customer_id == customer.id,
                    Consent.client_name == "Demo Budgeting App",
                )
            )
            if not consent:
                db.add(
                    Consent(
                        customer_id=customer.id,
                        client_name="Demo Budgeting App",
                        scopes=["accounts:read", "payments:write"],
                        status="ACTIVE",
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )
                )

            cbdc_wallet = db.scalar(
                select(CbdcWallet).where(CbdcWallet.customer_id == customer.id)
            )
            if not cbdc_wallet:
                cbdc_wallet = CbdcWallet(
                    customer_id=customer.id,
                    owner_label=f"{full_name} ePKR Wallet",
                    balance=Decimal("5000.00"),
                    currency="ePKR",
                    status="ACTIVE",
                )
                db.add(cbdc_wallet)
                db.flush()
                db.add(
                    CbdcOperation(
                        reference=f"SEED-{cbdc_wallet.id[:12]}",
                        destination_wallet_id=cbdc_wallet.id,
                        operation_type="ISSUE",
                        amount=Decimal("5000.00"),
                        status="COMPLETED",
                    )
                )

        merchant_user = created["merchant@globalpay.example.com"]
        merchant = db.scalar(select(Merchant).where(Merchant.user_id == merchant_user.id))
        if not merchant:
            merchant = Merchant(
                user_id=merchant_user.id,
                business_name="GlobalMart",
                status="ACTIVE",
                settlement_config={"cycle": "T+1", "currency": "PKR"},
            )
            db.add(merchant)
            db.flush()
        merchant_wallet = db.scalar(select(Wallet).where(Wallet.merchant_id == merchant.id))
        if not merchant_wallet:
            db.add(
                Wallet(
                    merchant_id=merchant.id,
                    balance=Decimal("10000.00"),
                    currency="PKR",
                    status="ACTIVE",
                )
            )

        db.commit()
        print("Demo data ready.")
        print("Customer:  customer@globalpay.example.com / Customer123!")
        print("Receiver:  receiver@globalpay.example.com / Receiver123!")
        print("Merchant:  merchant@globalpay.example.com / Merchant123!")
        print("Analyst:   analyst@globalpay.example.com / Analyst123!")
        print("Executive: executive@globalpay.example.com / Executive123!")
        print("Admin:     admin@globalpay.example.com / Admin123!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
