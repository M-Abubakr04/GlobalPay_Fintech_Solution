# Security Scan Report

**Scan date:** 3 September 2026
**Scope:** Repository source, configuration, dependency manifests, Dockerfiles, and Kubernetes manifests

## Results

| Tool | Scope | Result | Evidence |
|---|---|---|---|
| Semgrep | 89 files, 489 applicable rules | **0 findings** after remediating the initial Docker non-root finding | `semgrep-report.json` |
| Trivy filesystem scan | Vulnerabilities, secrets, misconfiguration | 2 medium dependency findings; 0 secrets; 36 configuration findings | `trivy-filesystem-report.json` |
| npm audit | Production and development dependency tree | High-severity `nanoid` issue remediated; 2 moderate React Router findings remain | `frontend/package-lock.json` |

## Remediation and residual risk

- The backend image now creates and runs as the unprivileged `globalpay` user, resolving the Semgrep
  `missing-user-entrypoint` finding.
- `nanoid` was updated to 3.3.18 through a non-breaking lockfile update.
- The remaining React Router findings require React Router 7, a breaking major-version migration.
  This proof of concept uses neither server-side hydration nor user-controlled redirect targets, reducing
  exposure to the reported paths. Migration to React Router 7 remains a tracked production-hardening action.
- Trivy configuration findings primarily concern defense-in-depth settings for local Compose/Kubernetes
  demonstrations. They must be reviewed and risk-treated before any real deployment.
- No secret was detected in the repository scan. `.env` remains excluded from version control.

## Interpretation

The scans provide DevSecOps evidence and informed risk treatment. They do not prove that the project is
vulnerability-free and do not represent PCI DSS, ISO, or other formal certification.
