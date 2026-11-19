#!/bin/bash

# Retry function with exponential backoff
retry() {
  local max_attempts=5
  local delay=5
  local attempt=1
  until "$@"; do
    if (( attempt == max_attempts )); then
      echo "Command failed after $attempt attempts."
      return 1
    fi
    echo "Command failed. Retrying in $delay seconds... (Attempt $((attempt+1))/$max_attempts)"
    sleep $delay
    attempt=$(( attempt + 1 ))
    delay=$(( delay * 2 ))
  done
}

# Wait until a line containing $1 appears in file $2, failing after $3 seconds
wait_for_line() {
  local pattern="$1"
  local file="$2"
  local timeout="$3"
  local waited=0
  until grep -qF "$pattern" "$file" 2>/dev/null; do
    if (( waited >= timeout )); then
      echo "ERROR: '$pattern' did not appear in $file after ${timeout}s" >&2
      tail -50 "$file" >&2 2>/dev/null || true
      return 1
    fi
    sleep 2
    waited=$(( waited + 2 ))
  done
  echo "'$pattern' found in $file after ${waited}s"
}
