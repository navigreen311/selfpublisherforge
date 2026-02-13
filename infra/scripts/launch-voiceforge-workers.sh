#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Launch 30 Headless Claude Code Workers for VoiceForge
# ==============================================================================
# Launches Claude Code in headless mode for each VoiceForge worktree.
# Each worker reads its prompt from prompts/voiceforge/VF##-*.md
#
# Usage: bash infra/scripts/launch-voiceforge-workers.sh [start] [end]
#   Examples:
#     bash infra/scripts/launch-voiceforge-workers.sh          # All 30
#     bash infra/scripts/launch-voiceforge-workers.sh 1 10     # VF01-VF10
#     bash infra/scripts/launch-voiceforge-workers.sh 14 22    # VF14-VF22
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-vf-worktrees"
PROMPTS_DIR="$PROJECT_ROOT/prompts/voiceforge"
LOG_DIR="$PROJECT_ROOT/logs/voiceforge"

START=${1:-1}
END=${2:-30}

mkdir -p "$LOG_DIR"

echo "============================================"
echo " VoiceForge — Launching Workers $START-$END"
echo "============================================"
echo ""

# Map worker numbers to prompt files and worktree dirs
declare -A WORKER_MAP
WORKER_MAP[1]="vf01:VF01-audiobook-models.md"
WORKER_MAP[2]="vf02:VF02-dictation-models.md"
WORKER_MAP[3]="vf03:VF03-audiobook-schemas-core.md"
WORKER_MAP[4]="vf04:VF04-audiobook-schemas-generation.md"
WORKER_MAP[5]="vf05:VF05-dictation-schemas.md"
WORKER_MAP[6]="vf06:VF06-config-docker-deps.md"
WORKER_MAP[7]="vf07:VF07-tts-engine.md"
WORKER_MAP[8]="vf08:VF08-asr-engine.md"
WORKER_MAP[9]="vf09:VF09-audio-processor.md"
WORKER_MAP[10]="vf10:VF10-voice-manager.md"
WORKER_MAP[11]="vf11:VF11-provider-router.md"
WORKER_MAP[12]="vf12:VF12-ssml-generator.md"
WORKER_MAP[13]="vf13:VF13-dictation-refiner.md"
WORKER_MAP[14]="vf14:VF14-audiobook-crud-router.md"
WORKER_MAP[15]="vf15:VF15-audiobook-generation-router.md"
WORKER_MAP[16]="vf16:VF16-audiobook-mastering-router.md"
WORKER_MAP[17]="vf17:VF17-audiobook-ssml-pronunciation-router.md"
WORKER_MAP[18]="vf18:VF18-dictation-router.md"
WORKER_MAP[19]="vf19:VF19-celery-audiobook-tasks.md"
WORKER_MAP[20]="vf20:VF20-celery-mastering-tasks.md"
WORKER_MAP[21]="vf21:VF21-ws-audiobook-progress.md"
WORKER_MAP[22]="vf22:VF22-ws-dictation-streaming.md"
WORKER_MAP[23]="vf23:VF23-frontend-audiobook-types-hooks.md"
WORKER_MAP[24]="vf24:VF24-frontend-audiobook-studio.md"
WORKER_MAP[25]="vf25:VF25-frontend-voice-picker-cost.md"
WORKER_MAP[26]="vf26:VF26-frontend-chapter-audio-player.md"
WORKER_MAP[27]="vf27:VF27-frontend-ssml-acx-export.md"
WORKER_MAP[28]="vf28:VF28-frontend-dictation-types-hooks.md"
WORKER_MAP[29]="vf29:VF29-frontend-dictation-components.md"
WORKER_MAP[30]="vf30:VF30-integration-registration.md"

LAUNCHED=0

for i in $(seq $START $END); do
    entry="${WORKER_MAP[$i]}"
    if [ -z "$entry" ]; then
        echo "  SKIP  Worker $i — no mapping"
        continue
    fi

    IFS=':' read -r worktree_id prompt_file <<< "$entry"
    worktree_dir="$WORKTREE_BASE/$worktree_id"
    prompt_path="$PROMPTS_DIR/$prompt_file"
    log_file="$LOG_DIR/${worktree_id}.log"

    if [ ! -d "$worktree_dir" ]; then
        echo "  SKIP  $worktree_id — worktree not found at $worktree_dir"
        continue
    fi

    if [ ! -f "$prompt_path" ]; then
        echo "  SKIP  $worktree_id — prompt not found at $prompt_path"
        continue
    fi

    echo "  LAUNCH $worktree_id ($prompt_file)"
    echo "    Worktree: $worktree_dir"
    echo "    Log: $log_file"

    # Read prompt content
    PROMPT_CONTENT=$(cat "$prompt_path")

    # Launch Claude Code in headless mode
    # Each worker gets its own worktree as CWD
    cd "$worktree_dir"
    claude --dangerously-skip-permissions \
        -p "You are working in a git worktree at $worktree_dir on branch $(git branch --show-current).

Read the CLAUDE.md file first for project conventions.

Your task:
$PROMPT_CONTENT

After completing the implementation:
1. Run any relevant linting/type checks
2. Fix any issues found
3. Stage and commit your changes with a conventional commit message (feat: ...)
4. Do NOT push — the merge script will handle that

IMPORTANT: Only create/modify files specified in your task. Do not modify files that other workers are responsible for." \
        > "$log_file" 2>&1 &

    LAUNCHED=$((LAUNCHED + 1))

    # Small delay to avoid API rate limits
    sleep 2
done

cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo " Launched $LAUNCHED workers"
echo " Logs at: $LOG_DIR/"
echo "============================================"
echo ""
echo "Monitor progress:"
echo "  tail -f $LOG_DIR/vf*.log"
echo ""
echo "Check status:"
echo "  bash infra/scripts/monitor-voiceforge-workers.sh"
