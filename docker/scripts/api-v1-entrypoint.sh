#!/bin/bash
set -e

echo "=== Copying API v1 source ==="
rsync -a --exclude='.git' --exclude='node_modules' --exclude='logs' \
  --exclude='files' --exclude='coverage' --exclude='.clinic' --exclude='.claude' \
  /mnt/src/ /app/

# Create writable directories
mkdir -p /app/logs /app/files/attachments /app/files/pdfs /app/files/temp

# Install openreview-py (needed by PythonShell in setup scripts)
# Copy to writable temp dir since source is mounted read-only
echo "=== Installing openreview-py ==="
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.egg-info' /mnt/openreview-py/ /tmp/openreview-py/
pip3 install --break-system-packages -q /tmp/openreview-py

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

echo "=== Starting API v1 ==="
NODE_ENV=circleci node scripts/clean_start_app.js
