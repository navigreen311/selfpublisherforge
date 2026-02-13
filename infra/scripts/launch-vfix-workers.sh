#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Launch 30 Headless Claude Code Workers for VoiceForge Fix
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-vfix-worktrees"
PROMPTS_DIR="$PROJECT_ROOT/prompts/voiceforge-fix"
LOG_DIR="$PROJECT_ROOT/logs/voiceforge-fix"

START=${1:-1}
END=${2:-30}

mkdir -p "$LOG_DIR"

echo "============================================"
echo " VoiceForge Fix — Launching Workers $START-$END"
echo "============================================"
echo ""

declare -A WORKER_MAP
WORKER_MAP[1]="fix01:FIX01-audiobook-crud-router.md"
WORKER_MAP[2]="fix02:FIX02-audiobook-crud-service.md"
WORKER_MAP[3]="fix03:FIX03-voice-mgmt-router.md"
WORKER_MAP[4]="fix04:FIX04-voice-mgmt-service.md"
WORKER_MAP[5]="fix05:FIX05-mastering-router.md"
WORKER_MAP[6]="fix06:FIX06-mastering-service.md"
WORKER_MAP[7]="fix07:FIX07-export-router.md"
WORKER_MAP[8]="fix08:FIX08-export-service.md"
WORKER_MAP[9]="fix09:FIX09-schemas-extended.md"
WORKER_MAP[10]="fix10:FIX10-register-routers.md"
WORKER_MAP[11]="fix11:FIX11-python-deps-migration.md"
WORKER_MAP[12]="fix12:FIX12-backend-import-verify.md"
WORKER_MAP[13]="fix13:FIX13-audiobook-types-complete.md"
WORKER_MAP[14]="fix14:FIX14-dictation-types-complete.md"
WORKER_MAP[15]="fix15:FIX15-audiobook-studio-page.md"
WORKER_MAP[16]="fix16:FIX16-audiobook-detail-page.md"
WORKER_MAP[17]="fix17:FIX17-project-list-component.md"
WORKER_MAP[18]="fix18:FIX18-new-project-dialog.md"
WORKER_MAP[19]="fix19:FIX19-voice-preview-modal.md"
WORKER_MAP[20]="fix20:FIX20-generation-queue-panel.md"
WORKER_MAP[21]="fix21:FIX21-audiobook-settings-panel.md"
WORKER_MAP[22]="fix22:FIX22-loading-error-states.md"
WORKER_MAP[23]="fix23:FIX23-keyboard-shortcuts.md"
WORKER_MAP[24]="fix24:FIX24-test-tts-asr.md"
WORKER_MAP[25]="fix25:FIX25-test-audio-processor.md"
WORKER_MAP[26]="fix26:FIX26-test-voice-provider.md"
WORKER_MAP[27]="fix27:FIX27-test-ssml-dictation.md"
WORKER_MAP[28]="fix28:FIX28-test-audiobook-crud.md"
WORKER_MAP[29]="fix29:FIX29-test-dictation-service.md"
WORKER_MAP[30]="fix30:FIX30-final-integration-verify.md"

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

    PROMPT_CONTENT=$(cat "$prompt_path")

    cd "$worktree_dir"
    claude --dangerously-skip-permissions \
        -p "You are working in a git worktree at $worktree_dir on branch $(git branch --show-current).

Read the CLAUDE.md file first for project conventions.

Your task:
$PROMPT_CONTENT

After completing the implementation:
1. Run any relevant linting/type checks
2. Fix any issues found
3. Stage and commit your changes with a conventional commit message (fix: ...)
4. Do NOT push — the merge script will handle that

IMPORTANT: Only create/modify files specified in your task. Do not modify files that other workers are responsible for." \
        > "$log_file" 2>&1 &

    LAUNCHED=$((LAUNCHED + 1))
    sleep 2
done

cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo " Launched $LAUNCHED workers"
echo " Logs at: $LOG_DIR/"
echo "============================================"
