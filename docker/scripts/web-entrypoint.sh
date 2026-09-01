#!/bin/bash
set -e

echo "=== Copying web source ==="
rsync -a --exclude='.git' --exclude='node_modules' --exclude='.next' \
  --exclude='videos' /mnt/src/ /app/

# Use .env.example as base, override SUPER_USER for test environment
cp /app/.env.example /app/.env.local
sed -i 's/SUPER_USER=.*/SUPER_USER=openreview.net/' /app/.env.local

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

echo "=== Starting web dev server ==="
export NEXT_PORT=3030
SUPER_USER=openreview.net exec npm run dev
