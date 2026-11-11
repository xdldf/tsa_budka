#!/usr/bin/env bash
set -euo pipefail

PROJECT="/home/user/job/VEF_budka_v2"
BACKEND_DIR="$PROJECT/backend"
FRONTEND_DIR="$PROJECT/frontend"
UVICORN="$BACKEND_DIR/.venv/bin/uvicorn"
ELECTRON="$FRONTEND_DIR/node_modules/electron/dist/electron"
BACKEND_PORT=8000
HEALTH_URL="http://localhost:${BACKEND_PORT}/health"

# --- Backend ---
cd "$BACKEND_DIR"
"$UVICORN" app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

shutdown() {
  kill "${BACKEND_PID}" 2>/dev/null || true
  if [ -n "$ELECTRON_PID" ]; then
    kill "$ELECTRON_PID" 2>/dev/null || true
  fi
}
trap shutdown EXIT
trap shutdown INT

# Wait for the backend to become healthy (or give up after ~90s).
waited=0
while [ "$waited" -lt 90 ]; do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  waited=$((waited + 2))
done

# --- Kiosk window (starts the Next.js server itself) ---
cd "$FRONTEND_DIR"
"$ELECTRON" . --no-sandbox &
ELECTRON_PID=$!

wait "$ELECTRON_PID"