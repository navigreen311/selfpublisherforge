#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Run Full Test Suite
# ==============================================================================
# Runs all tests: backend (pytest), frontend (jest), and reports results.
#
# Usage: bash infra/scripts/test-all.sh [--backend-only] [--frontend-only]
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

BACKEND_ONLY=false
FRONTEND_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only) BACKEND_ONLY=true; shift ;;
        --frontend-only) FRONTEND_ONLY=true; shift ;;
        *) shift ;;
    esac
done

echo "============================================"
echo " SelfPublisherForge — Test Suite"
echo " $(date)"
echo "============================================"
echo ""

BACKEND_PASS=0
BACKEND_FAIL=0
FRONTEND_PASS=0
FRONTEND_FAIL=0

# Backend Tests
if [ "$FRONTEND_ONLY" = false ]; then
    echo "--- Backend Tests (pytest) ---"
    cd "$PROJECT_ROOT/backend"

    if [ -f "requirements.txt" ]; then
        # Ensure venv and deps
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
        pip install -r requirements.txt -q 2>/dev/null

        # Run tests
        if python -m pytest tests/ -v --tb=short --no-header -q 2>&1; then
            echo "Backend tests: PASSED"
            BACKEND_PASS=1
        else
            echo "Backend tests: SOME FAILURES"
            BACKEND_FAIL=1
        fi

        deactivate 2>/dev/null || true
    else
        echo "No requirements.txt found, skipping backend tests"
    fi
    echo ""
fi

# Frontend Tests
if [ "$BACKEND_ONLY" = false ]; then
    echo "--- Frontend Tests (jest) ---"
    cd "$PROJECT_ROOT/frontend"

    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            npm install --silent 2>/dev/null
        fi

        if npx jest --passWithNoTests --no-coverage 2>&1; then
            echo "Frontend tests: PASSED"
            FRONTEND_PASS=1
        else
            echo "Frontend tests: SOME FAILURES"
            FRONTEND_FAIL=1
        fi
    else
        echo "No package.json found, skipping frontend tests"
    fi
    echo ""
fi

# Summary
echo "============================================"
echo " Test Summary"
echo "============================================"
[ "$FRONTEND_ONLY" = false ] && printf " Backend:  %s\n" "$([ $BACKEND_FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL')"
[ "$BACKEND_ONLY" = false ] && printf " Frontend: %s\n" "$([ $FRONTEND_FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "============================================"

# Exit code
if [ $BACKEND_FAIL -gt 0 ] || [ $FRONTEND_FAIL -gt 0 ]; then
    exit 1
fi
exit 0
