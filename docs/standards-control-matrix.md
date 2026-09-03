# Standards and Control Implementation Matrix

This project is **standards-aligned**, not formally certified. Every row identifies a practical implementation and evidence location.

| Standard / Framework | Applied control | Implementation | Evidence |
|---|---|---|---|
| ISO/IEC 27001 | Access control, auditability, risk-based security | JWT, RBAC, correlation IDs, audit logs, environment-based secrets | `backend/app/core/security.py`, `api/deps.py`, `core/audit.py` |
| ISO/IEC 27017 | Cloud workload security | Non-root application container, isolated Compose network, environment-injected secrets, health checks and read-only dataset mount | `backend/Dockerfile`, `compose.yaml`, `.env.example` |
| ISO/IEC 27018 | Protect customer PII | AES-GCM field encryption, masked API responses, no PII in audit metadata | `core/security.py`, `modules/customers/router.py`, `tests/test_security.py` |
| NIST SP 800-63 | Digital identity lifecycle | Registration validation, account status, registration validation, account status, authentication assurance and simulated KYC status | `modules/auth/`, `modules/customers/` |
| OAuth 2.0 / JWT | Authenticated API access | OAuth2 password form for the PoC, signed bearer access tokens and role claims | `/api/v1/auth/login`, Swagger Authorize |
| OpenID Connect (OIDC) | Future enterprise federation | Identified as the future identity layer for enterprise IdP integration; not falsely claimed as implemented in the local PoC | `README.md`, `docs/architecture/ADR-001-modular-monolith.md` |
| OWASP Top 10 | Web application security | Authentication, authorization, secure configuration, input validation and safe error handling | `backend/app/`, `frontend/src/` |
| OWASP API Top 10 | API-specific security risks | Current-user wallet ownership, Pydantic schemas, RBAC, scoped access, rate limiting and bounded limits | `modules/wallets/`, `modules/payments/`, `api/deps.py`, `core/rate_limit.py` |
| PCI DSS v4.0 | Card-data exposure reduction | No PAN, CVV or PIN is accepted or stored; payments use simulated wallet IDs | payment schemas and scope statement |
| ISO 20022 | Financial message consistency | Stable transaction reference, currency, amount, party/wallet and status fields | `models/entities.py`, payment and PIS responses |
| ISO/IEC 42001 | AI governance | Model registry, version, features, metrics, threshold and human accountability | `modules/fraud/service.py`, `model_registry` |
| NIST AI RMF | Govern, map, measure and manage AI risk | Dataset/version records, model metrics, explainable reasons, human review and investigation history | `modules/fraud/`, `docs/reports/AI_MODEL_EVALUATION.md` |
| Open Banking standards | Consent-based AIS/PIS | Scoped consent, expiry, account ownership, API-call audit and payment initiation simulation | `modules/open_banking/` |
| NIST Cybersecurity Framework 2.0 | Govern, identify, protect, detect, respond and recover | RBAC/security controls, audit logs, monitoring metrics, test evidence and recovery scripts | `backend/app/core/`, `monitoring/`, `scripts/backup_database.sh` |
| CIS Critical Security Controls | Practical safeguards | Secure configuration, account/access control, logging, vulnerability scanning and application security evidence | `.gitignore`, `scripts/run_security_scans.sh`, `backend/app/core/` |
| COBIT 2019 | Governance and reporting | Read-only executive KPIs, report export and audit evidence | `modules/dashboard/`, Executive React page |

## Important limitation

References to PCI DSS, ISO 27017, OIDC and formal certification are conceptual or future-alignment statements unless explicitly identified above as implemented controls.
