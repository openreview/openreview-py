#!/bin/bash
# PreToolUse hook: runs setup-testing.sh before pytest commands

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only act on commands that invoke pytest as a command (not filenames containing "pytest")
if ! echo "$COMMAND" | grep -qE '(^|&& |; |\| )pytest '; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/../scripts/setup-testing.sh"

if [ ! -x "$SETUP_SCRIPT" ]; then
  echo "Setup script not found or not executable: $SETUP_SCRIPT" >&2
  exit 2
fi

echo "Running test environment setup before pytest..." >&2
if ! bash "$SETUP_SCRIPT"; then
  echo "Test environment setup failed. Blocking pytest." >&2
  exit 2
fi

exit 0
