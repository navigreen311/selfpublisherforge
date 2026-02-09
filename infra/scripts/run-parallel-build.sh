#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Master Orchestration Script
# ==============================================================================
# Complete parallel build: create worktrees -> launch 30 workers -> monitor ->
# test -> merge -> cleanup.
#
# Usage: bash infra/scripts/run-parallel-build.sh
#
# Stages:
#   1. Create 30 git worktrees
#   2. Launch 30 headless Claude Code instances
#   3. Monitor until all complete
#   4. Run tests in each worktree
#   5. Merge all branches into main (tier-ordered)
#   6. Run full test suite on merged code
#   7. Cleanup worktrees
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo " SelfPublisherForge — Parallel Build Orchestrator"
echo " $(date)"
echo "============================================================"
echo ""
echo " Project: $PROJECT_ROOT"
echo ""
echo " This will:"
echo "   1. Create 30 git worktrees"
echo "   2. Launch 30 Claude Code headless workers"
echo "   3. Wait for all workers to complete"
echo "   4. Test each branch"
echo "   5. Merge all branches into main"
echo "   6. Run full test suite"
echo "   7. Cleanup"
echo ""
read -p " Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# ──────────────────────────────────────────
# Stage 1: Create Worktrees
# ──────────────────────────────────────────
echo ""
echo "=== Stage 1: Creating Worktrees ==="
bash "$SCRIPT_DIR/create-worktrees.sh"

# ──────────────────────────────────────────
# Stage 2: Launch Workers
# ──────────────────────────────────────────
echo ""
echo "=== Stage 2: Launching 30 Workers ==="
bash "$SCRIPT_DIR/launch-workers.sh"

# ──────────────────────────────────────────
# Stage 3: Monitor Progress
# ──────────────────────────────────────────
echo ""
echo "=== Stage 3: Monitoring Progress ==="
echo "Workers are running in background. Monitoring..."
echo ""

PID_DIR="$PROJECT_ROOT/infra/pids"
while true; do
    RUNNING=0
    TOTAL=0
    for pid_file in "$PID_DIR"/*.pid; do
        [ -f "$pid_file" ] || continue
        TOTAL=$((TOTAL + 1))
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            RUNNING=$((RUNNING + 1))
        fi
    done

    COMPLETED=$((TOTAL - RUNNING))
    echo "  [$(date +%H:%M:%S)] Running: $RUNNING / $TOTAL | Completed: $COMPLETED"

    if [ $RUNNING -eq 0 ] && [ $TOTAL -gt 0 ]; then
        echo ""
        echo "  All workers completed!"
        break
    fi

    sleep 30
done

# Show final status
bash "$SCRIPT_DIR/monitor-workers.sh"

# ──────────────────────────────────────────
# Stage 4: Test Each Branch (optional)
# ──────────────────────────────────────────
echo ""
echo "=== Stage 4: Quick Validation ==="
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-worktrees"

for w in $(seq -w 1 30); do
    worker_id="w$w"
    worktree_dir="$WORKTREE_BASE/$worker_id"
    if [ -d "$worktree_dir" ]; then
        echo -n "  $worker_id: "
        # Check if there are any Python syntax errors
        (cd "$worktree_dir" && python3 -c "import ast; import glob; [ast.parse(open(f).read()) for f in glob.glob('backend/**/*.py', recursive=True)]" 2>/dev/null) \
            && echo "Python OK" || echo "Python WARN"
    fi
done

# ──────────────────────────────────────────
# Stage 5: Merge All Branches
# ──────────────────────────────────────────
echo ""
echo "=== Stage 5: Merging Branches ==="
bash "$SCRIPT_DIR/merge-workers.sh" --skip-tests

# ──────────────────────────────────────────
# Stage 6: Full Test Suite
# ──────────────────────────────────────────
echo ""
echo "=== Stage 6: Full Test Suite ==="
bash "$SCRIPT_DIR/test-all.sh" || {
    echo ""
    echo "Some tests failed. Review and fix before pushing."
}

# ──────────────────────────────────────────
# Stage 7: Cleanup
# ──────────────────────────────────────────
echo ""
read -p "=== Stage 7: Cleanup worktrees? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/cleanup-worktrees.sh"
fi

echo ""
echo "============================================================"
echo " Build Complete!"
echo "============================================================"
echo ""
echo " Next steps:"
echo "   1. Review merged code: git log --oneline -30"
echo "   2. Fix any remaining test failures"
echo "   3. Push to remote: git push origin main"
echo ""
