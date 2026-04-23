#!/bin/bash
set -e

echo "=== Copying API v1 source ==="
rsync -a --exclude='.git' --exclude='node_modules' --exclude='logs' \
  --exclude='files' --exclude='coverage' --exclude='.clinic' --exclude='.claude' \
  /mnt/src/ /app/

# Create writable directories
mkdir -p /app/logs /app/files/attachments /app/files/pdfs /app/files/temp

# Install openreview-py into a persistent venv (needed by PythonShell)
# Editable install: .py changes are picked up without reinstall.
# Only runs full pip install when pyproject.toml changes (new deps).
VENV=/opt/venv
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.egg-info' /mnt/openreview-py/ /tmp/openreview-py/

if [ ! -f "$VENV/bin/activate" ]; then
    python3 -m venv "$VENV"
fi

PY_HASH=$(md5sum /tmp/openreview-py/pyproject.toml | cut -d' ' -f1)
CACHED_PY_HASH=""
[ -f "$VENV/.hash" ] && CACHED_PY_HASH=$(cat "$VENV/.hash")
if [ "$PY_HASH" != "$CACHED_PY_HASH" ]; then
    echo "=== Installing openreview-py ==="
    "$VENV/bin/pip" install -q -e /tmp/openreview-py
    echo "$PY_HASH" > "$VENV/.hash"
else
    echo "=== openreview-py up to date, skipping install ==="
fi

# Make venv's python available to PythonShell
export VIRTUAL_ENV="$VENV"
export PATH="$VENV/bin:$PATH"

# npm install with caching (skip if package-lock.json unchanged)
LOCK_HASH=$(md5sum /app/package-lock.json | cut -d' ' -f1)
CACHED_HASH=""
[ -f /app/node_modules/.lock-hash ] && CACHED_HASH=$(cat /app/node_modules/.lock-hash)
if [ "$LOCK_HASH" != "$CACHED_HASH" ]; then
    echo "=== Installing npm dependencies ==="
    npm ci
    echo "$LOCK_HASH" > /app/node_modules/.lock-hash
else
    echo "=== npm dependencies up to date, skipping install ==="
fi

rm -f /tmp/setup-complete
if [ "${CLEAN_START}" = "false" ]; then
  echo "=== Starting API v1 (preserving database) ==="
  NODE_ENV=circleci npm run start 2>&1 | while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -q "Server is listening on port"; then
      touch /tmp/setup-complete
    fi
  done
else
  echo "=== Starting API v1 (clean database) ==="
  NODE_ENV=circleci node scripts/clean_start_app.js 2>&1 | while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -q "Setup Complete!"; then
      touch /tmp/setup-complete
    fi
  done
fi
