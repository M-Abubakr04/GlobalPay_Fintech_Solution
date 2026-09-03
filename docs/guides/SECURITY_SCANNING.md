# Security Scanning Guide

## Semgrep

```bash
python3 -m pip install semgrep
semgrep scan --config auto backend frontend
```

## Trivy

Install Trivy using its official package instructions, then run:

```bash
trivy fs --scanners vuln,secret,misconfig .
trivy image globalpay-backend
trivy image globalpay-frontend
```

Or use:

```bash
bash scripts/run_security_scans.sh
```

Store exported evidence under `docs/reports/`.

## Scope

A clean scan does not establish formal security certification. Findings should be documented, prioritised and retested.
