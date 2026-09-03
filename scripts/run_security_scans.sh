#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p docs/reports

if command -v semgrep >/dev/null 2>&1; then
  semgrep scan --config auto backend frontend \
    --json-output docs/reports/semgrep-report.json || true
else
  echo "Semgrep is not installed. Run: python3 -m pip install semgrep" \
    | tee docs/reports/semgrep-report.txt
fi

if command -v trivy >/dev/null 2>&1; then
  trivy fs --scanners vuln,secret,misconfig \
    --format json --output docs/reports/trivy-filesystem-report.json . || true
else
  echo "Trivy is not installed. See docs/guides/SECURITY_SCANNING.md" \
    | tee docs/reports/trivy-report.txt
fi

echo "Security scan evidence written to docs/reports/"
