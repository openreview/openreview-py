#!/usr/bin/env bash
set -euo pipefail

find tests -type f -name 'test_*.py' | sort
