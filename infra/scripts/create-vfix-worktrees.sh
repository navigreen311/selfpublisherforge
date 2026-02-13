#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Create 30 Git Worktrees for VoiceForge Fix Round
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-vfix-worktrees"
BASE_BRANCH="ai-feature/voiceforge-integration"

echo "============================================"
echo " VoiceForge Fix — Worktree Setup"
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

git checkout "$BASE_BRANCH"
mkdir -p "$WORKTREE_BASE"

declare -a WORKERS=(
    "fix01:ai-fix/vf-audiobook-crud-router"
    "fix02:ai-fix/vf-audiobook-crud-service"
    "fix03:ai-fix/vf-voice-mgmt-router"
    "fix04:ai-fix/vf-voice-mgmt-service"
    "fix05:ai-fix/vf-mastering-router"
    "fix06:ai-fix/vf-mastering-service"
    "fix07:ai-fix/vf-export-router"
    "fix08:ai-fix/vf-export-service"
    "fix09:ai-fix/vf-schemas-extended"
    "fix10:ai-fix/vf-register-routers"
    "fix11:ai-fix/vf-python-deps-migration"
    "fix12:ai-fix/vf-backend-import-verify"
    "fix13:ai-fix/vf-audiobook-types"
    "fix14:ai-fix/vf-dictation-types"
    "fix15:ai-fix/vf-studio-list-page"
    "fix16:ai-fix/vf-studio-detail-page"
    "fix17:ai-fix/vf-project-list-component"
    "fix18:ai-fix/vf-new-project-dialog"
    "fix19:ai-fix/vf-voice-preview-modal"
    "fix20:ai-fix/vf-generation-queue-panel"
    "fix21:ai-fix/vf-settings-panel"
    "fix22:ai-fix/vf-loading-error-states"
    "fix23:ai-fix/vf-keyboard-shortcuts"
    "fix24:ai-fix/vf-test-tts-asr"
    "fix25:ai-fix/vf-test-audio-processor"
    "fix26:ai-fix/vf-test-voice-provider"
    "fix27:ai-fix/vf-test-ssml-dictation"
    "fix28:ai-fix/vf-test-audiobook-crud"
    "fix29:ai-fix/vf-test-dictation-service"
    "fix30:ai-fix/vf-final-verify"
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
echo "============================================"
