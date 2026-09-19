#!/usr/bin/env bash
# Apply database migrations, then exec the given command (the API server).
# Idempotent: `alembic upgrade head` is a no-op when already current.
set -euo pipefail

echo "[entrypoint] applying migrations…"
alembic upgrade head

echo "[entrypoint] starting: $*"
exec "$@"
