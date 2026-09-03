#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p backups
timestamp="$(date +%Y%m%d_%H%M%S)"
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-globalpay}" \
  -d "${POSTGRES_DB:-globalpay}" \
  --clean --if-exists \
  > "backups/globalpay_${timestamp}.sql"
echo "Created backups/globalpay_${timestamp}.sql"
