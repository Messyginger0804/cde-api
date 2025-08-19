#!/usr/bin/env bash
set -euo pipefail

# Start the FastAPI app, auto-creating a virtualenv and installing deps.
# Usage: ./scripts/start.sh [--port 8000] [--host 0.0.0.0]

HOST="127.0.0.1"
PORT="8000"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="$2"; shift 2;;
    --port)
      PORT="$2"; shift 2;;
    *)
      echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

# Move to repo root (this script lives in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Create a Python virtualenv if missing
PY_BIN="python3"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  PY_BIN="python"
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv in .venv ..."
  "$PY_BIN" -m venv .venv
fi
source .venv/bin/activate

echo "Upgrading pip and installing requirements ..."
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

# Create a default .env if missing
if [[ ! -f .env ]]; then
  cat > .env <<'EOF'
API_TOKEN=devtoken
# DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
EOF
  echo "Created default .env with API_TOKEN=devtoken"
fi

# Default to a local SQLite DB for quick runs if DATABASE_URL isn't set
export DATABASE_URL=${DATABASE_URL:-sqlite:///./dev.db}

echo "Starting API on http://${HOST}:${PORT} (docs at /docs)"
echo "DATABASE_URL=${DATABASE_URL}"

exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
