#!/bin/bash
# Kill all test services (ports 3000, 3001, 3030)

echo "Stopping services on ports 3000, 3001, 3030..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3030 | xargs kill -9 2>/dev/null || true
echo "Done."
