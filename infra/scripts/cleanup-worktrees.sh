#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Cleanup Worktrees
# ==============================================================================
# Remove all 30 worktrees after successful merge. Keeps branches intact.
#
# Usage: bash infra/scripts/cleanup-worktrees.sh [--delete-branches]
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-worktrees"

DELETE_BRANCHES=false
[ "$1" = "--delete-branches" ] && DELETE_BRANCHES=true

cd "$PROJECT_ROOT"

echo "============================================"
echo " SelfPublisherForge — Cleanup Worktrees"
echo "============================================"
echo ""

# Remove each worktree
for w in $(seq -w 1 30); do
    worker_id="w$w"
    worktree_dir="$WORKTREE_BASE/$worker_id"

    if [ -d "$worktree_dir" ]; then
        echo "  REMOVE $worker_id -> $worktree_dir"
        git worktree remove "$worktree_dir" --force 2>/dev/null || {
            rm -rf "$worktree_dir"
            git worktree prune
        }
    fi
done

# Clean up base directory
rmdir "$WORKTREE_BASE" 2>/dev/null || true

# Optionally delete branches
if [ "$DELETE_BRANCHES" = true ]; then
    echo ""
    echo "Deleting feature branches..."
    for branch in $(git branch --list 'ai-feature/*'); do
        branch=$(echo "$branch" | tr -d ' *')
        echo "  DELETE $branch"
        git branch -D "$branch" 2>/dev/null || true
    done
fi

# Clean up logs and pids
rm -rf "$PROJECT_ROOT/infra/logs" "$PROJECT_ROOT/infra/pids" 2>/dev/null || true

echo ""
echo "Cleanup complete."
git worktree list
