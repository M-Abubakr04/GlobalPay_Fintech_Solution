#!/usr/bin/env bash
set -Eeuo pipefail

base="${BASE_URL:-http://localhost:8000}"

curl -fsS "$base/health/live" | python3 -m json.tool
curl -fsS "$base/health/ready" | python3 -m json.tool

token="$(
  curl -fsS -X POST "$base/api/v1/auth/login" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode 'username=customer@globalpay.example.com' \
    --data-urlencode 'password=Customer123!' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

curl -fsS "$base/api/v1/wallets/me" \
  -H "Authorization: Bearer $token" | python3 -m json.tool

echo "GlobalPay smoke test passed."
