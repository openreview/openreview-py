#!/bin/bash
# PreToolUse hook: verifies Docker is available before run.py commands

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only act on commands that invoke run.py (the Docker Compose dev tool)
if ! echo "$COMMAND" | grep -qE '(^|&& |; |\| |/| )run\.py( |$)'; then
  exit 0
fi

# Verify Docker daemon is running
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running. Start Docker Desktop or the Docker daemon first." >&2
  echo "Install Docker: https://docs.docker.com/get-docker/" >&2
  exit 2
fi

exit 0
