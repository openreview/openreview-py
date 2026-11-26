#!/usr/bin/env bash
set -euo pipefail

find tests -type f \( -path 'tests/test_*.py' -o -path 'tests/unit_tests/test_*.py' \) | sort
