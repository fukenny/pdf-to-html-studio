#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

# Codex includes a working Python runtime on this Mac. Prefer it when Apple's
# developer-tools Python launcher is unavailable or misconfigured.
codex_python="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -x "$codex_python" ]; then
  PYTHONPATH=src exec "$codex_python" local-app/server.py
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3 was not found. Install Python 3.11 or newer and try again.\n'
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv || exit 1
  .venv/bin/pip install -e . || exit 1
fi
exec .venv/bin/python local-app/server.py
