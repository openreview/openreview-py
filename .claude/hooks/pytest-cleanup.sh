#!/bin/bash
# PostToolUse hook: kills test servers after pytest commands

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only act on pytest commands
if ! echo "$COMMAND" | grep -qE '(^|&& |; |\| )pytest '; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$SCRIPT_DIR/../scripts/stop-testing.sh" >&2

exit 0
