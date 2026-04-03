#!/bin/bash
set -e

cd "$(dirname "$0")"

# Start infrastructure services (idempotent if already running)
echo "=== Starting infrastructure ==="
docker compose up -d --wait mongo redis elasticsearch web

# Force recreate API servers to run cleanStart (cleans DB, creates objects)
# Infrastructure (mongo, redis, ES, web) stays running untouched.
echo "=== Restarting API servers (clean database) ==="
docker compose rm -sf api-v1 api-v2

# Start api-v2 which depends on api-v1 — both get recreated and wait for healthy
docker compose up -d --wait api-v2

# Run tests (passes all arguments through to pytest)
echo "=== Running tests ==="
docker compose run --rm test "$@"
