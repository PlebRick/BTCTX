#!/bin/bash
#
# Pre-Commit Test Script for BitcoinTX
#
# Run this before every commit, especially when modifying backend code.
#
# Usage:
#   ./scripts/pre-commit.sh          # Full test suite (requires backend running)
#   ./scripts/pre-commit.sh --quick  # Quick tests only
#   ./scripts/pre-commit.sh --no-api # Static checks only (no backend needed)
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo ""
echo "========================================"
echo "  BitcoinTX Pre-Commit Tests"
echo "========================================"
echo ""

# Check if we should start the backend
if [[ "$*" != *"--no-api"* ]]; then
    # Check if backend is running
    if ! curl -s http://127.0.0.1:8000/api/accounts/ > /dev/null 2>&1; then
        echo "Backend not running. Starting it..."
        echo ""

        # Start backend in background
        uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
        BACKEND_PID=$!

        # Wait for backend to be ready
        echo "Waiting for backend to start..."
        for i in {1..30}; do
            if curl -s http://127.0.0.1:8000/api/accounts/ > /dev/null 2>&1; then
                echo "Backend started (PID: $BACKEND_PID)"
                break
            fi
            sleep 1
        done

        if ! curl -s http://127.0.0.1:8000/api/accounts/ > /dev/null 2>&1; then
            echo "ERROR: Backend failed to start"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi

        # Trap to kill backend on exit
        trap "echo ''; echo 'Stopping backend...'; kill $BACKEND_PID 2>/dev/null || true" EXIT
    else
        echo "Backend already running at http://127.0.0.1:8000"
    fi
fi

echo ""

# Run the Python test suite
python3 backend/tests/pre_commit_tests.py "$@"

EXIT_CODE=$?

exit $EXIT_CODE
