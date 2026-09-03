-- GlobalPay PostgreSQL schema reference.
-- Source of truth in the running application: backend/app/models/entities.py.
-- This file mirrors the 14 SQLAlchemy entities for assessment/review purposes.

CREATE TABLE model_registry (
    id VARCHAR(36) PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    feature_list_json JSON NOT NULL,
    metrics_json JSON NOT NULL,
    threshold NUMERIC(5,4) NOT NULL,
    is_active BOOLEAN NOT NULL,
    trained_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE customers (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id),
    full_name VARCHAR(180) NOT NULL,
    phone_encrypted TEXT,
    national_id_encrypted TEXT,
    kyc_status VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ix_customers_user_id ON customers (user_id);

CREATE TABLE merchants (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE REFERENCES users(id),
    business_name VARCHAR(200) NOT NULL,
    status VARCHAR(30) NOT NULL,
    settlement_config JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ix_merchants_user_id ON merchants (user_id);

CREATE TABLE wallets (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) UNIQUE REFERENCES customers(id),
    merchant_id VARCHAR(36) UNIQUE REFERENCES merchants(id),
    balance NUMERIC(18,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_wallet_balance_nonnegative CHECK (balance >= 0),
    CONSTRAINT ck_wallet_exactly_one_owner CHECK (
        (customer_id IS NOT NULL AND merchant_id IS NULL) OR
        (customer_id IS NULL AND merchant_id IS NOT NULL)
    )
);
CREATE UNIQUE INDEX ix_wallets_customer_id ON wallets (customer_id);
CREATE UNIQUE INDEX ix_wallets_merchant_id ON wallets (merchant_id);

CREATE TABLE consents (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id),
    client_name VARCHAR(150) NOT NULL,
    scopes JSON NOT NULL,
    status VARCHAR(30) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_consents_customer_id ON consents (customer_id);

CREATE TABLE api_calls (
    id VARCHAR(36) PRIMARY KEY,
    consent_id VARCHAR(36) REFERENCES consents(id),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    latency_ms NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_api_calls_consent_id ON api_calls (consent_id);
CREATE INDEX ix_api_calls_created_endpoint ON api_calls (created_at, endpoint);

CREATE TABLE transactions (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(40) UNIQUE NOT NULL,
    sender_wallet_id VARCHAR(36) REFERENCES wallets(id),
    receiver_wallet_id VARCHAR(36) REFERENCES wallets(id),
    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL,
    channel VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL,
    description VARCHAR(255),
    idempotency_key VARCHAR(100) NOT NULL,
    risk_score NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_transactions_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT ck_transaction_amount_positive CHECK (amount > 0)
);
CREATE UNIQUE INDEX ix_transactions_reference ON transactions (reference);
CREATE INDEX ix_transactions_created_status ON transactions (created_at, status);
CREATE INDEX ix_transactions_sender_wallet_id ON transactions (sender_wallet_id);
CREATE INDEX ix_transactions_receiver_wallet_id ON transactions (receiver_wallet_id);

CREATE TABLE ledger_entries (
    id VARCHAR(36) PRIMARY KEY,
    transaction_id VARCHAR(36) NOT NULL REFERENCES transactions(id),
    wallet_id VARCHAR(36) NOT NULL REFERENCES wallets(id),
    entry_type VARCHAR(10) NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    balance_after NUMERIC(18,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_ledger_amount_positive CHECK (amount > 0),
    CONSTRAINT ck_ledger_entry_type CHECK (entry_type IN ('DEBIT','CREDIT'))
);
CREATE INDEX ix_ledger_entries_transaction_id ON ledger_entries (transaction_id);
CREATE INDEX ix_ledger_entries_wallet_id ON ledger_entries (wallet_id);
CREATE INDEX ix_ledger_wallet_created ON ledger_entries (wallet_id, created_at);

CREATE TABLE fraud_alerts (
    id VARCHAR(36) PRIMARY KEY,
    transaction_id VARCHAR(36) UNIQUE NOT NULL REFERENCES transactions(id),
    risk_score NUMERIC(5,4) NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    risk_band VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    reasons_json JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ix_fraud_alerts_transaction_id ON fraud_alerts (transaction_id);

CREATE TABLE investigations (
    id VARCHAR(36) PRIMARY KEY,
    alert_id VARCHAR(36) NOT NULL REFERENCES fraud_alerts(id),
    analyst_user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    decision VARCHAR(30) NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_investigations_alert_id ON investigations (alert_id);

CREATE TABLE cbdc_wallets (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) REFERENCES customers(id),
    owner_label VARCHAR(180) NOT NULL,
    balance NUMERIC(18,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_cbdc_wallets_customer_id ON cbdc_wallets (customer_id);

CREATE TABLE cbdc_operations (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(40) UNIQUE NOT NULL,
    source_wallet_id VARCHAR(36) REFERENCES cbdc_wallets(id),
    destination_wallet_id VARCHAR(36) REFERENCES cbdc_wallets(id),
    operation_type VARCHAR(30) NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    actor_user_id VARCHAR(36) REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id VARCHAR(36),
    correlation_id VARCHAR(64),
    metadata_json JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs (actor_user_id);
CREATE INDEX ix_audit_logs_correlation_id ON audit_logs (correlation_id);
CREATE INDEX ix_audit_created_entity ON audit_logs (created_at, entity_type);
