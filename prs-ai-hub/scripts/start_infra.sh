#!/usr/bin/env bash
# Start only Postgres and Redis (for local .venv backend development).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose up -d postgres redis

echo "Waiting for Postgres..."
until docker compose exec -T postgres pg_isready -U prs_user -d prs_db &>/dev/null; do
  sleep 1
done

echo "Postgres and Redis are up."
echo "  DATABASE_URL=postgresql+asyncpg://prs_user:prs_password@localhost:5432/prs_db"
echo "  REDIS_URL=redis://localhost:6379/0"
