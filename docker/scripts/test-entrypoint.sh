#!/bin/bash
set -e

echo "=== Setting up test environment ==="
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' \
  /mnt/src/ /app/

cd /app

echo "=== Installing openreview-py ==="
pip install -q -c requirements.txt -e .

echo "=== Installing test dependencies ==="
pip install -q -c requirements-dev.txt -e '.[test]'

# Link geckodriver (installed in Dockerfile to /usr/local/bin)
mkdir -p /app/tests/drivers
ln -sf /usr/local/bin/geckodriver /app/tests/drivers/geckodriver

echo "=== Running tests ==="
exec pytest "$@"
