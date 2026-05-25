#!/usr/bin/env bash
# Run all 4 FastAPI services locally using .venv (Postgres + Redis via Docker recommended).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "No .venv found. Run: ./scripts/setup_venv.sh"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

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
export SUPPLIER_AGENT_URL="${SUPPLIER_AGENT_URL:-http://localhost:8005}"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///${ROOT}/data/prs_local.db}"
export DATA_DIR="${DATA_DIR:-$ROOT/data}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"

PIDS=()
cleanup() {
  echo ""
  echo "Stopping backend services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting intake agent on :8001 ..."
(cd "$ROOT/backend/agents/intake" && uvicorn main:app --host 0.0.0.0 --port 8001 --reload) &
PIDS+=($!)

echo "Starting contract agent on :8002 ..."
(cd "$ROOT/backend/agents/contract" && uvicorn main:app --host 0.0.0.0 --port 8002 --reload) &
PIDS+=($!)

echo "Starting SKU agent on :8003 ..."
(cd "$ROOT/backend/agents/sku" && uvicorn main:app --host 0.0.0.0 --port 8003 --reload) &
PIDS+=($!)

echo "Starting CCR agent on :8004 ..."
(cd "$ROOT/backend/agents/ccr" && uvicorn main:app --host 0.0.0.0 --port 8004 --reload) &
PIDS+=($!)

echo "Starting supplier agent on :8005 ..."
(cd "$ROOT/backend/agents/supplier" && uvicorn main:app --host 0.0.0.0 --port 8005 --reload) &
PIDS+=($!)

echo "Starting gateway on :8000 ..."
(cd "$ROOT/backend/gateway" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload) &
PIDS+=($!)

echo ""
echo "Backend running:"
echo "  Gateway   http://localhost:8000/docs"
echo "  Intake    http://localhost:8001/health"
echo "  Contract  http://localhost:8002/health"
echo "  SKU       http://localhost:8003/health"
echo "  CCR       http://localhost:8004/health"
echo "  Supplier  http://localhost:8005/health"
echo ""
echo "Press Ctrl+C to stop all services."
wait
