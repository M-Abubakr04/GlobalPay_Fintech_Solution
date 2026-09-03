# Submission Readiness Review

**Reviewed against:** the assigned Enterprise Capstone Project topic, EduQual assessment/certification
guide, and Examination Readiness & Presentation Compliance Instructions supplied by the student.
**Review date:** 3 September 2026

## Repository deliverables

| Requirement | Status | Evidence |
|---|---|---|
| Complete FastAPI and React source | Ready | `backend/`, `frontend/` |
| PostgreSQL schema and simulated dataset | Ready | `database/schema.sql`, `datasets/transactions.csv` |
| Customer/wallet management | Ready | Customer and wallet modules plus UI |
| Payment processing and financial reporting | Ready | Payments module, Reports UI, CSV export |
| AI-assisted fraud detection and evaluation | Ready | Fraud module, dataset, model evaluation report |
| Open Banking and CBDC simulation | Ready | Open Banking/CBDC modules and UI |
| Executive dashboard and reports | Ready | Executive and Reports routes, JSON export |
| Dockerfiles and Docker Compose | Ready | Full stack verified; configurable host ports |
| Optional Kubernetes manifests | Included | `k8s/` |
| All 17 mandatory diagrams | Ready | PDF and editable PPTX diagram pack |
| API documentation and testing assets | Ready | OpenAPI/Swagger/ReDoc and Postman collection |
| Installation, deployment, user, admin guides | Ready | `docs/guides/` |
| Test, AI, security, API reports | Ready | `docs/reports/` |
| Standards/framework alignment | Ready | `docs/standards-control-matrix.md` |
| Comprehensive README | Ready | Objectives, architecture, deployment, limits, tests, assumptions, future work |

## Operational addresses

Default host ports are frontend 3000, backend 8000, Prometheus 9090, and Grafana 3001. They are
independently configurable in `.env`; internal service ports stay fixed. This avoids local port clashes
without breaking Nginx proxying, health checks, or Prometheus service discovery.

## Items outside repository verification

These are personal/institutional submission actions and cannot be proven by source-code inspection:

- Student portal MCQ, lecture, internship, lab, and live-class completion thresholds.
- A separately prepared 15–20 minute Stage 1 presentation and personal viva readiness.
- Replying in the original exam-topic email thread with both the GitHub URL and one complete folder.
- GitHub authentication and the final remote repository URL.

The student must understand and independently defend the architecture, trade-offs, security controls,
failure/recovery behavior, standards alignment, and AI governance. AI-assisted code or documentation
does not replace that requirement.
