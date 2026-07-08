#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PY="$ROOT/backend/.venv/bin/python"

kill_pid_file() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 0
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  kill -- "-$pid" >/dev/null 2>&1 || kill "$pid" >/dev/null 2>&1 || true
}

wait_for_ports_free() {
  for _ in {1..20}; do
    if ! fuser 8000/tcp 3000/tcp >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

rm_rf_retry() {
  for _ in {1..10}; do
    rm -rf "$@" && return 0
    sleep 0.25
  done
  rm -rf "$@"
}

codespaces_url() {
  local port="$1"
  if command -v gh >/dev/null 2>&1 && [[ -n "${CODESPACE_NAME:-}" ]]; then
    gh codespace ports -c "$CODESPACE_NAME" --json sourcePort,browseUrl --jq ".[] | select(.sourcePort == $port) | .browseUrl" 2>/dev/null || true
  fi
}

maybe_make_frontend_public() {
  command -v gh >/dev/null 2>&1 || return 0
  [[ -n "${CODESPACE_NAME:-}" ]] || return 0

  local auto_public="${PICKPILOT_PUBLIC_FRONTEND_PORT:-auto}"
  if [[ "$auto_public" == "0" ]]; then
    return 0
  fi

  local current_visibility
  current_visibility="$(gh codespace ports -c "$CODESPACE_NAME" --json sourcePort,visibility --jq '.[] | select(.sourcePort == 3000) | .visibility' 2>/dev/null || true)"
  if [[ "$current_visibility" == "public" ]]; then
    return 0
  fi

  echo "Making Codespaces frontend port 3000 public..."
  gh codespace ports visibility 3000:public -c "$CODESPACE_NAME" >/dev/null 2>&1 || true
}

warn_if_private_frontend() {
  local url="$1"
  [[ "$url" == http://127.0.0.1:* ]] && return 0
  local headers
  headers="$(curl -sS -I --max-time 10 "$url" 2>/dev/null | tr -d '\r' || true)"
  if grep -qi "www-authenticate: tunnel" <<<"$headers" || grep -qi "location: https://github.dev/pf-signin" <<<"$headers"; then
    echo
    echo "Port 3000 is private or requires GitHub auth in this browser session."
    echo "If this URL shows 404, open it while signed into GitHub, or run: PICKPILOT_PUBLIC_FRONTEND_PORT=1 ./start.sh"
  fi
}

echo "Clearing app caches..."
mkdir -p logs
kill_pid_file logs/backend.pid
kill_pid_file logs/frontend.pid
fuser -k 8000/tcp 3000/tcp >/dev/null 2>&1 || true
wait_for_ports_free || true
rm_rf_retry frontend/.next .pytest_cache logs/backend.log logs/frontend.log
find backend frontend -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +

if [[ ! -x "$PY" ]]; then
  python3 -m venv backend/.venv
fi

echo "Installing backend dependencies..."
"$PY" -m pip install -r backend/requirements.txt >/dev/null

echo "Installing frontend dependencies..."
npm install --prefix frontend --no-audit --no-fund >/dev/null

echo "Starting PostgreSQL..."
docker compose up -d postgres

echo "Running migrations..."
"$PY" -m alembic -c backend/alembic.ini upgrade head

echo "Starting backend on 0.0.0.0:8000 ..."
setsid "$PY" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting frontend on 0.0.0.0:3000 ..."
setsid bash -lc 'cd frontend && exec npm run dev -- --hostname 0.0.0.0 --port 3000' > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

cleanup() {
  trap - EXIT INT TERM
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
wait_for "Frontend root" "http://127.0.0.1:3000/" "$FRONTEND_PID" "logs/frontend.log"
wait_for "Frontend products" "http://127.0.0.1:3000/products" "$FRONTEND_PID" "logs/frontend.log"

maybe_make_frontend_public
FRONTEND_URL="$(codespaces_url 3000)"
BACKEND_URL="$(codespaces_url 8000)"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
warn_if_private_frontend "$FRONTEND_URL"

echo "Ready:"
echo "  Frontend:           ${FRONTEND_URL}"
echo "  Frontend products:  ${FRONTEND_URL}/products"
echo "  Backend API:        ${BACKEND_URL}"
echo
echo "Logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo
echo "Press Ctrl+C to stop both servers."

wait -n "$BACKEND_PID" "$FRONTEND_PID"
