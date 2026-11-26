#!/usr/bin/env bash
# Runs each test file in its own pytest process so that pytest.ini's -x stops only
# the failing file, not the remaining files assigned to this node.
set -uo pipefail

junit_dir=$1
shift
mkdir -p "$junit_dir"

if [ "$#" -eq 0 ]; then
  echo "No test files assigned to this node"
  exit 0
fi

failed=0
for test_file in "$@"; do
  pytest "$test_file" --durations=0 -v -o junit_family=legacy \
    -o junit_suite_name="$test_file" --junitxml="$junit_dir/${test_file//\//_}.xml" || failed=1
done

exit "$failed"
