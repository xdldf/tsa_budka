#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
/opt/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

shutdown() {
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap shutdown EXIT

cd /app/frontend
# GL runs on mesa (llvmpipe software fallback) since host GPU drivers are not
# available inside the container. --disable-dev-shm-usage avoids black windows
# caused by Docker's tiny default /dev/shm. Override via ELECTRON_EXTRA_FLAGS.
npx electron . --no-sandbox ${ELECTRON_EXTRA_FLAGS:---disable-dev-shm-usage}
