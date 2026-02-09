#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Create 30 Git Worktrees for Parallel Development
# ==============================================================================
# This script creates 30 separate worktrees from the main branch,
# each on its own feature branch, ready for a headless Claude Code instance.
#
# Usage: bash infra/scripts/create-worktrees.sh
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-worktrees"

echo "============================================"
echo " SelfPublisherForge — Worktree Setup"
echo "============================================"
echo "Project root: $PROJECT_ROOT"
echo "Worktrees at: $WORKTREE_BASE"
echo ""

# Ensure we're in the git repo
cd "$PROJECT_ROOT"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not a git repository. Run this from the project root."
    exit 1
fi

# Ensure main branch has at least one commit
if ! git log -1 > /dev/null 2>&1; then
    echo "ERROR: No commits yet. Commit the scaffold first."
    exit 1
fi

# Create worktree base directory
mkdir -p "$WORKTREE_BASE"

# Define all 30 worker branches
declare -a WORKERS=(
    "w01:ai-feature/project-scaffold"
    "w02:ai-feature/database-schema"
    "w03:ai-feature/auth-system"
    "w04:ai-feature/user-org-management"
    "w05:ai-feature/billing-subscriptions"
    "w06:ai-feature/file-storage"
    "w07:ai-feature/notifications"
    "w08:ai-feature/frontend-shell"
    "w09:ai-feature/api-gateway"
    "w10:ai-feature/websocket-realtime"
    "w11:ai-feature/task-queue-events"
    "w12:ai-feature/devops-infrastructure"
    "w13:ai-feature/market-intelligence"
    "w14:ai-feature/ai-writing-studio"
    "w15:ai-feature/style-cloning"
    "w16:ai-feature/llm-orchestration"
    "w17:ai-feature/knowledge-vault"
    "w18:ai-feature/production-pipeline"
    "w19:ai-feature/publishing-ops"
    "w20:ai-feature/kdp-validation"
    "w21:ai-feature/product-page-lab"
    "w22:ai-feature/pricing-automation"
    "w23:ai-feature/competitor-finder"
    "w24:ai-feature/marketing-launch"
    "w25:ai-feature/advertising-intelligence"
    "w26:ai-feature/review-intelligence"
    "w27:ai-feature/analytics-bi"
    "w28:ai-feature/agent-system"
    "w29:ai-feature/portfolio-economics"
    "w30:ai-feature/chrome-ext-covers"
)

CREATED=0
SKIPPED=0

for entry in "${WORKERS[@]}"; do
    IFS=':' read -r worker_id branch_name <<< "$entry"
    worktree_dir="$WORKTREE_BASE/$worker_id"

    if [ -d "$worktree_dir" ]; then
        echo "  SKIP  $worker_id ($branch_name) — worktree already exists"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "  CREATE $worker_id -> $worktree_dir ($branch_name)"
    git worktree add -b "$branch_name" "$worktree_dir" HEAD 2>/dev/null || \
    git worktree add "$worktree_dir" "$branch_name" 2>/dev/null || \
    {
        echo "    WARN: Branch $branch_name may already exist, trying checkout..."
        git worktree add "$worktree_dir" "$branch_name" 2>/dev/null || \
        git branch -D "$branch_name" 2>/dev/null
        git worktree add -b "$branch_name" "$worktree_dir" HEAD
    }
    CREATED=$((CREATED + 1))
done

echo ""
echo "============================================"
echo " Done: $CREATED created, $SKIPPED skipped"
echo " Worktrees at: $WORKTREE_BASE"
echo "============================================"
echo ""
echo "List worktrees:"
git worktree list
