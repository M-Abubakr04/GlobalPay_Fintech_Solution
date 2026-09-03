# ADR-001: Use a Modular Monolith for the Proof of Concept

## Status

Accepted.

## Context

GlobalPay must demonstrate five connected FinTech modules on a laptop with 8–16 GB RAM. Wallet transfers require strong transactional consistency, while the live assessment needs a reliable and understandable deployment.

## Decision

Use one FastAPI deployment unit with bounded internal modules:

- authentication/customer/wallet
- payments/ledger
- fraud AI
- Open Banking/CBDC
- executive reporting

React, PostgreSQL, Redis, Prometheus and Grafana remain separate containers.

## Consequences

### Positive

- A payment debit, credit, transaction record and double-entry ledger can commit atomically.
- One authentication and migration boundary reduces live-demo risk.
- Code boundaries remain clear through routers, schemas, services and repositories.
- The deployment stays laptop-friendly.

### Trade-offs

- Modules cannot be independently scaled or deployed.
- A backend failure affects all application modules.
- Future extraction requires explicit API/event contracts.

## Future evolution

When transaction scale, team ownership or independent deployment justifies it, extract modules behind an API gateway and introduce a transactional outbox/event bus. This is a future enhancement, not part of the current assessment implementation.
