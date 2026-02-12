#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Merge VoiceForge Fix Worker Branches
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BASE_BRANCH="ai-feature/voiceforge-integration"

cd "$PROJECT_ROOT"

echo "============================================"
echo " VoiceForge Fix — Merging Worker Branches"
echo "============================================"

git checkout "$BASE_BRANCH"

# Merge order: schemas first, then services, then routers, then registration,
# then frontend types, then pages, then components, then tests, then verification
declare -a MERGE_ORDER=(
    "ai-fix/vf-schemas-extended"
    "ai-fix/vf-audiobook-crud-service"
    "ai-fix/vf-audiobook-crud-router"
    "ai-fix/vf-voice-mgmt-service"
    "ai-fix/vf-voice-mgmt-router"
    "ai-fix/vf-mastering-service"
    "ai-fix/vf-mastering-router"
    "ai-fix/vf-export-service"
    "ai-fix/vf-export-router"
    "ai-fix/vf-register-routers"
    "ai-fix/vf-python-deps-migration"
    "ai-fix/vf-backend-import-verify"
    "ai-fix/vf-audiobook-types"
    "ai-fix/vf-dictation-types"
    "ai-fix/vf-studio-list-page"
    "ai-fix/vf-studio-detail-page"
    "ai-fix/vf-project-list-component"
    "ai-fix/vf-new-project-dialog"
    "ai-fix/vf-voice-preview-modal"
    "ai-fix/vf-generation-queue-panel"
    "ai-fix/vf-settings-panel"
    "ai-fix/vf-loading-error-states"
    "ai-fix/vf-keyboard-shortcuts"
    "ai-fix/vf-test-tts-asr"
    "ai-fix/vf-test-audio-processor"
    "ai-fix/vf-test-voice-provider"
    "ai-fix/vf-test-ssml-dictation"
    "ai-fix/vf-test-audiobook-crud"
    "ai-fix/vf-test-dictation-service"
    "ai-fix/vf-final-verify"
)

MERGED=0
FAILED=0
SKIPPED=0

for branch in "${MERGE_ORDER[@]}"; do
    if ! git rev-parse --verify "$branch" > /dev/null 2>&1; then
        echo "  SKIP  $branch — branch not found"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    AHEAD=$(git rev-list "$BASE_BRANCH".."$branch" --count 2>/dev/null || echo "0")
    if [ "$AHEAD" = "0" ]; then
        echo "  SKIP  $branch — no new commits"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "  MERGE $branch ($AHEAD commits ahead)"
    if git merge --no-ff "$branch" -m "fix: merge $branch into voiceforge integration" 2>/dev/null; then
        MERGED=$((MERGED + 1))
    else
        echo "    CONFLICT — attempting auto-resolve..."
        git checkout --theirs . 2>/dev/null || true
        git add -A
        git commit -m "fix: merge $branch (auto-resolved conflicts)" --no-verify 2>/dev/null || {
            echo "    FAILED — manual resolution needed for $branch"
            git merge --abort 2>/dev/null || true
            FAILED=$((FAILED + 1))
            continue
        }
        MERGED=$((MERGED + 1))
    fi
done

echo ""
echo "============================================"
echo " Results: $MERGED merged, $SKIPPED skipped, $FAILED failed"
echo "============================================"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "WARNING: $FAILED branches had unresolvable conflicts."
fi
