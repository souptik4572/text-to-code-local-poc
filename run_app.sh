#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "Error: .venv not found. Create it first with: python3 -m venv .venv"
  exit 1
fi

source .venv/bin/activate

echo "Starting backend on http://localhost:8000 ..."
uvicorn backend.main:app --reload --reload-dir backend --port 8000 &
BACKEND_PID=$!

wait_for_backend() {
  echo "Waiting for backend health endpoint ..."
  for _ in {1..30}; do
    if python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=1)" >/dev/null 2>&1; then
      echo "Backend is healthy."
      return 0
    fi
    sleep 1
  done

  echo "Error: backend did not become healthy within 30 seconds."
  return 1
}

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "Stopping backend (PID: $BACKEND_PID) ..."
    kill "$BACKEND_PID"
  fi
}
trap cleanup EXIT INT TERM

wait_for_backend

echo "Starting frontend on http://localhost:8501 ..."
streamlit run frontend/app.py --server.runOnSave true --server.fileWatcherType auto
