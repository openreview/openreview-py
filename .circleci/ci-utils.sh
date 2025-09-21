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
