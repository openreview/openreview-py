#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$PROJECT_DIR/.claude/test-runner-env.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found at $CONFIG_FILE" >&2
  echo "Run the /test-runner skill first to set up your environment." >&2
  exit 1
fi

# Read config
ENV_ACTIVATION=$(jq -r '.env_activation' "$CONFIG_FILE")
API_V1_PATH=$(jq -r '.api_v1_path' "$CONFIG_FILE")
API_V2_PATH=$(jq -r '.api_v2_path' "$CONFIG_FILE")
WEB_PATH=$(jq -r '.web_path' "$CONFIG_FILE")

if [ "$WEB_PATH" = "null" ] || [ -z "$WEB_PATH" ]; then
  echo "Error: web_path not set in $CONFIG_FILE" >&2
  echo "Run the /test-runner skill to add the openreview-web path." >&2
  exit 1
fi

mkdir -p "$PROJECT_DIR/.claude/logs"

# ---- Kill all existing services ----
echo "Killing services on ports 3000, 3001, 3030..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3030 | xargs kill -9 2>/dev/null || true
sleep 2

# ---- Start openreview-web (port 3030) ----
echo "Starting openreview-web on port 3030..."
cd "$WEB_PATH"
SUPER_USER=openreview.net npx next dev --port 3030 > $PROJECT_DIR/.claude/logs/openreview-web.log 2>&1 &
WEB_PID=$!
disown $WEB_PID

# Poll for port 3030
ELAPSED=0
TIMEOUT=60
while ! lsof -ti:3030 >/dev/null 2>&1; do
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "Error: openreview-web did not start within ${TIMEOUT}s" >&2
    echo "Check $PROJECT_DIR/.claude/logs/openreview-web.log for details" >&2
    exit 1
  fi
  sleep 3
  ELAPSED=$((ELAPSED + 3))
done
echo "openreview-web is listening on port 3030 (${ELAPSED}s)"

# ---- Start API v1 (port 3000) ----
echo "Starting API v1 on port 3000..."
V1_LOG="$PROJECT_DIR/.claude/logs/api-v1-stdout.log"
cd "$API_V1_PATH"
bash -c "$ENV_ACTIVATION && npm run cleanStart" > "$V1_LOG" 2>&1 &
V1_PID=$!
disown $V1_PID

# Poll for "Setup Complete!" in stdout (the string is printed to stdout, not the server's log file)
ELAPSED=0
TIMEOUT=120
while ! grep -q "Setup Complete!" "$V1_LOG" 2>/dev/null; do
  if ! kill -0 $V1_PID 2>/dev/null; then
    echo "Error: API v1 process died. Check $V1_LOG" >&2
    exit 1
  fi
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "Error: API v1 did not complete setup within ${TIMEOUT}s. Check $V1_LOG" >&2
    exit 1
  fi
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done
echo "API v1 is ready on port 3000 (${ELAPSED}s)"

# ---- Start API v2 (port 3001) ----
echo "Starting API v2 on port 3001..."
V2_LOG="$PROJECT_DIR/.claude/logs/api-v2-stdout.log"
cd "$API_V2_PATH"
bash -c "$ENV_ACTIVATION && npm run cleanStart" > "$V2_LOG" 2>&1 &
V2_PID=$!
disown $V2_PID

# Poll for "Setup Complete!" in stdout (the string is printed to stdout, not the server's log file)
ELAPSED=0
TIMEOUT=120
while ! grep -q "Setup Complete!" "$V2_LOG" 2>/dev/null; do
  if ! kill -0 $V2_PID 2>/dev/null; then
    echo "Error: API v2 process died. Check $V2_LOG" >&2
    exit 1
  fi
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "Error: API v2 did not complete setup within ${TIMEOUT}s. Check $V2_LOG" >&2
    exit 1
  fi
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done
echo "API v2 is ready on port 3001 (${ELAPSED}s)"

echo ""
echo "All services are ready:"
echo "  - openreview-web: http://localhost:3030"
echo "  - API v1:         http://localhost:3000"
echo "  - API v2:         http://localhost:3001"
