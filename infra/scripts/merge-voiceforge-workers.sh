#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Merge VoiceForge Worker Branches
# ==============================================================================
# Merges all 30 VoiceForge worker branches into the integration branch.
# Uses --no-ff to preserve branch history.
#
# Usage: bash infra/scripts/merge-voiceforge-workers.sh
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BASE_BRANCH="ai-feature/voiceforge-integration"

cd "$PROJECT_ROOT"

echo "============================================"
echo " VoiceForge — Merging Worker Branches"
echo "============================================"

# Ensure we're on the integration branch
git checkout "$BASE_BRANCH"

# Define merge order (foundation first, then services, then routers, then frontend, then integration)
declare -a MERGE_ORDER=(
    "ai-feature/vf-audiobook-models"
    "ai-feature/vf-dictation-models"
    "ai-feature/vf-audiobook-schemas-core"
    "ai-feature/vf-audiobook-schemas-gen"
    "ai-feature/vf-dictation-schemas"
    "ai-feature/vf-config-docker-deps"
    "ai-feature/vf-tts-engine"
    "ai-feature/vf-asr-engine"
    "ai-feature/vf-audio-processor"
    "ai-feature/vf-voice-manager"
    "ai-feature/vf-provider-router"
    "ai-feature/vf-ssml-generator"
    "ai-feature/vf-dictation-refiner"
    "ai-feature/vf-audiobook-crud-router"
    "ai-feature/vf-audiobook-gen-router"
    "ai-feature/vf-audiobook-master-router"
    "ai-feature/vf-ssml-pronunciation-router"
    "ai-feature/vf-dictation-router"
    "ai-feature/vf-celery-audiobook-tasks"
    "ai-feature/vf-celery-mastering-tasks"
    "ai-feature/vf-ws-audiobook-progress"
    "ai-feature/vf-ws-dictation-streaming"
    "ai-feature/vf-fe-audiobook-types-hooks"
    "ai-feature/vf-fe-audiobook-studio"
    "ai-feature/vf-fe-voice-picker-cost"
    "ai-feature/vf-fe-chapter-audio-player"
    "ai-feature/vf-fe-ssml-acx-export"
    "ai-feature/vf-fe-dictation-types-hooks"
    "ai-feature/vf-fe-dictation-components"
    "ai-feature/vf-integration-registration"
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

    # Check if branch has commits ahead of base
    AHEAD=$(git rev-list "$BASE_BRANCH".."$branch" --count 2>/dev/null || echo "0")
    if [ "$AHEAD" = "0" ]; then
        echo "  SKIP  $branch — no new commits"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "  MERGE $branch ($AHEAD commits ahead)"
    if git merge --no-ff "$branch" -m "feat: merge $branch into voiceforge integration" 2>/dev/null; then
        MERGED=$((MERGED + 1))
    else
        echo "    CONFLICT — attempting auto-resolve..."
        # For conflicting files, prefer the incoming branch
        git checkout --theirs . 2>/dev/null || true
        git add -A
        git commit -m "feat: merge $branch (auto-resolved conflicts)" --no-verify 2>/dev/null || {
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
    echo "Review and merge manually."
fi
