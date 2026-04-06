#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

python "$ROOT/backend/init_db.py"
uvicorn main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" --app-dir "$ROOT/backend" &
BACKEND_PID=$!

npm --prefix "$ROOT/frontend" run dev -- --host 0.0.0.0
