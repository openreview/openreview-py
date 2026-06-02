#!/bin/bash
set -e

echo "=== Setting up test environment ==="
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' \
  /mnt/src/ /app/

cd /app

# Use a persistent venv (named volume) with editable install.
VENV=/opt/venv
if [ ! -f "$VENV/bin/activate" ]; then
    python -m venv "$VENV"
fi
source "$VENV/bin/activate"

PY_HASH=$(md5sum /app/pyproject.toml | cut -d' ' -f1)
CACHED_PY_HASH=""
[ -f "$VENV/.hash" ] && CACHED_PY_HASH=$(cat "$VENV/.hash")
if [ "$PY_HASH" != "$CACHED_PY_HASH" ]; then
    echo "=== Installing openreview-py and test dependencies ==="
    pip install -q -c requirements.txt -e .
    pip install -q -c requirements-dev.txt -e '.[test]'
    echo "$PY_HASH" > "$VENV/.hash"
else
    echo "=== Dependencies up to date, skipping install ==="
fi

# Link geckodriver
mkdir -p /app/tests/drivers
ln -sf /usr/local/bin/geckodriver /app/tests/drivers/geckodriver

echo "=== Shell ready (venv activated, run pytest as usual) ==="
exec bash
