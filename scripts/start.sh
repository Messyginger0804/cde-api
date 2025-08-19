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

# Load .env if present so PG* vars apply
if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

# Ensure Postgres config is present; either DATABASE_URL or PG* vars
if [[ -z "${DATABASE_URL:-}" ]]; then
  # If user filled PG* in .env, build DATABASE_URL
  PGHOST_DEFAULT=${PGHOST:-127.0.0.1}
  PGPORT_DEFAULT=${PGPORT:-5432}
  if [[ -n "${PGUSER:-}" && -n "${PGPASSWORD:-}" && -n "${PGDATABASE:-}" ]]; then
    export DATABASE_URL="postgresql+psycopg2://${PGUSER}:${PGPASSWORD}@${PGHOST_DEFAULT}:${PGPORT_DEFAULT}/${PGDATABASE}"
  else
    # Create a skeleton .env if missing or incomplete, then exit with guidance
    if ! grep -q '^PGUSER=' .env 2>/dev/null; then
      cat >> .env <<'EOF'
# PostgreSQL connection settings (fill these and rerun)
PGHOST=127.0.0.1
PGPORT=5432
PGUSER=
PGPASSWORD=
PGDATABASE=
EOF
      echo "Created/updated .env with PG* placeholders."
    fi
    echo "DATABASE_URL not set and PGUSER/PGPASSWORD/PGDATABASE not provided."
    echo "Please edit .env with your Postgres credentials or set DATABASE_URL."
    exit 1
  fi
fi

echo "Starting API on http://${HOST}:${PORT} (docs at /docs)"
echo "Using DATABASE_URL (PostgreSQL)"

exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
