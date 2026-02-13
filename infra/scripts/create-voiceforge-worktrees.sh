#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Create 30 Git Worktrees for VoiceForge Integration
# ==============================================================================
# Creates 30 worktrees from the voiceforge integration branch,
# each on its own feature branch, ready for a headless Claude Code instance.
#
# Usage: bash infra/scripts/create-voiceforge-worktrees.sh
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-vf-worktrees"
BASE_BRANCH="ai-feature/voiceforge-integration"

echo "============================================"
echo " VoiceForge Integration — Worktree Setup"
echo "============================================"
echo "Project root: $PROJECT_ROOT"
echo "Worktrees at: $WORKTREE_BASE"
echo "Base branch:  $BASE_BRANCH"
echo ""

cd "$PROJECT_ROOT"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not a git repository."
    exit 1
fi

# Ensure base branch exists
if ! git rev-parse --verify "$BASE_BRANCH" > /dev/null 2>&1; then
    echo "ERROR: Branch $BASE_BRANCH does not exist. Create it first."
    exit 1
fi

mkdir -p "$WORKTREE_BASE"

declare -a WORKERS=(
    "vf01:ai-feature/vf-audiobook-models"
    "vf02:ai-feature/vf-dictation-models"
    "vf03:ai-feature/vf-audiobook-schemas-core"
    "vf04:ai-feature/vf-audiobook-schemas-gen"
    "vf05:ai-feature/vf-dictation-schemas"
    "vf06:ai-feature/vf-config-docker-deps"
    "vf07:ai-feature/vf-tts-engine"
    "vf08:ai-feature/vf-asr-engine"
    "vf09:ai-feature/vf-audio-processor"
    "vf10:ai-feature/vf-voice-manager"
    "vf11:ai-feature/vf-provider-router"
    "vf12:ai-feature/vf-ssml-generator"
    "vf13:ai-feature/vf-dictation-refiner"
    "vf14:ai-feature/vf-audiobook-crud-router"
    "vf15:ai-feature/vf-audiobook-gen-router"
    "vf16:ai-feature/vf-audiobook-master-router"
    "vf17:ai-feature/vf-ssml-pronunciation-router"
    "vf18:ai-feature/vf-dictation-router"
    "vf19:ai-feature/vf-celery-audiobook-tasks"
    "vf20:ai-feature/vf-celery-mastering-tasks"
    "vf21:ai-feature/vf-ws-audiobook-progress"
    "vf22:ai-feature/vf-ws-dictation-streaming"
    "vf23:ai-feature/vf-fe-audiobook-types-hooks"
    "vf24:ai-feature/vf-fe-audiobook-studio"
    "vf25:ai-feature/vf-fe-voice-picker-cost"
    "vf26:ai-feature/vf-fe-chapter-audio-player"
    "vf27:ai-feature/vf-fe-ssml-acx-export"
    "vf28:ai-feature/vf-fe-dictation-types-hooks"
    "vf29:ai-feature/vf-fe-dictation-components"
    "vf30:ai-feature/vf-integration-registration"
)

CREATED=0
SKIPPED=0

for entry in "${WORKERS[@]}"; do
    IFS=':' read -r worker_id branch_name <<< "$entry"
    worktree_dir="$WORKTREE_BASE/$worker_id"

    if [ -d "$worktree_dir" ]; then
        echo "  SKIP  $worker_id ($branch_name) — already exists"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "  CREATE $worker_id -> $worktree_dir ($branch_name)"
    git worktree add -b "$branch_name" "$worktree_dir" "$BASE_BRANCH" 2>/dev/null || \
    git worktree add "$worktree_dir" "$branch_name" 2>/dev/null || \
    {
        echo "    WARN: Branch may exist, retrying..."
        git branch -D "$branch_name" 2>/dev/null
        git worktree add -b "$branch_name" "$worktree_dir" "$BASE_BRANCH"
    }
    CREATED=$((CREATED + 1))
done

echo ""
echo "============================================"
echo " Done: $CREATED created, $SKIPPED skipped"
echo " Worktrees at: $WORKTREE_BASE"
echo "============================================"
echo ""
echo "Worktree list:"
git worktree list
