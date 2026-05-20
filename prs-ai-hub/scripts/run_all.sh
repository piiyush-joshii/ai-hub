#!/usr/bin/env bash
# Run backend (4 services) + frontend in parallel — no Docker required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Run ./scripts/setup_venv.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q aiosqlite 2>/dev/null || true

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export INTAKE_AGENT_URL="${INTAKE_AGENT_URL:-http://localhost:8001}"
export CONTRACT_AGENT_URL="${CONTRACT_AGENT_URL:-http://localhost:8002}"
export SKU_AGENT_URL="${SKU_AGENT_URL:-http://localhost:8003}"
export CCR_AGENT_URL="${CCR_AGENT_URL:-http://localhost:8004}"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///${ROOT}/data/prs_local.db}"
export DATA_DIR="${DATA_DIR:-$ROOT/data}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
mkdir -p "$ROOT/data"

PIDS=()
cleanup() {
  echo ""
  echo "Stopping all services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting intake agent :8001 ..."
(cd "$ROOT/backend/agents/intake" && uvicorn main:app --host 0.0.0.0 --port 8001) &
PIDS+=($!)

echo "Starting contract agent :8002 ..."
(cd "$ROOT/backend/agents/contract" && uvicorn main:app --host 0.0.0.0 --port 8002) &
PIDS+=($!)

echo "Starting SKU agent :8003 ..."
(cd "$ROOT/backend/agents/sku" && uvicorn main:app --host 0.0.0.0 --port 8003) &
PIDS+=($!)

echo "Starting CCR agent :8004 ..."
(cd "$ROOT/backend/agents/ccr" && uvicorn main:app --host 0.0.0.0 --port 8004) &
PIDS+=($!)

echo "Starting gateway :8000 ..."
(cd "$ROOT/backend/gateway" && uvicorn main:app --host 0.0.0.0 --port 8000) &
PIDS+=($!)

sleep 2

echo "Starting frontend :3000 ..."
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi
(cd "$ROOT/frontend" && npm run dev) &
PIDS+=($!)

echo ""
echo "Running (no Docker):"
echo "  Frontend  http://localhost:3000"
echo "  API docs  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."
wait
