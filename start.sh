#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PY="$ROOT/backend/.venv/bin/python"

echo "Clearing app caches..."
rm -rf frontend/.next .pytest_cache
find backend frontend -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +

if [[ ! -x "$PY" ]]; then
  python3 -m venv backend/.venv
fi

echo "Installing backend dependencies..."
"$PY" -m pip install -r backend/requirements.txt >/dev/null

echo "Installing frontend dependencies..."
npm install --prefix frontend --no-audit --no-fund >/dev/null

echo "Freeing ports 8000 and 3000..."
fuser -k 8000/tcp 3000/tcp >/dev/null 2>&1 || true

echo "Starting PostgreSQL..."
docker compose up -d postgres

echo "Running migrations..."
"$PY" -m alembic -c backend/alembic.ini upgrade head

mkdir -p logs

echo "Starting backend on http://0.0.0.0:8000 ..."
setsid "$PY" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting frontend on http://0.0.0.0:3000 ..."
setsid bash -lc 'cd frontend && exec npm run dev -- --hostname 0.0.0.0 --port 3000' > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

cleanup() {
  echo
  echo "Stopping app..."
  kill -- "-$BACKEND_PID" "-$FRONTEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

wait_for() {
  local name="$1"
  local url="$2"
  local pid="$3"
  local log="$4"

  for _ in {1..30}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name is ready."
      return 0
    fi
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      echo "$name failed to start. Last log lines:"
      tail -40 "$log" || true
      return 1
    fi
    sleep 1
  done

  echo "$name did not become ready in time. Last log lines:"
  tail -40 "$log" || true
  return 1
}

wait_for "Backend" "http://127.0.0.1:8000/" "$BACKEND_PID" "logs/backend.log"
wait_for "Frontend" "http://127.0.0.1:3000/" "$FRONTEND_PID" "logs/frontend.log"

echo "Ready:"
echo "  Local frontend:     http://127.0.0.1:3000"
echo "  Local backend:      http://127.0.0.1:8000"
echo "  GitHub forwarded:   open the forwarded port 3000 URL"
echo
echo "Logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo
echo "Press Ctrl+C to stop both servers."

wait -n "$BACKEND_PID" "$FRONTEND_PID"
