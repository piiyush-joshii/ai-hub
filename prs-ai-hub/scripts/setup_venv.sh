#!/usr/bin/env bash
# Create .venv and install all Python dependencies for local development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" &>/dev/null; then
  echo "Error: $PYTHON not found. Install Python 3.11+ first."
  exit 1
fi

PY_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Using Python $PY_VERSION"

if [[ -d .venv ]]; then
  echo "Removing existing .venv ..."
  rm -rf .venv
fi

echo "Creating virtual environment at $ROOT/.venv ..."
"$PYTHON" -m venv .venv

# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -e ./shared/prs_models

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo ""
  echo "Created .env from .env.example — add your GROQ_API_KEY before running agents."
fi

echo ""
echo "Done. Activate the venv with:"
echo "  source .venv/bin/activate"
echo ""
echo "Then start Postgres/Redis (Docker) and backend services:"
echo "  ./scripts/run_backend.sh"
