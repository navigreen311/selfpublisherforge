#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Launch 30 Headless Claude Code Workers
# ==============================================================================
# Launches Claude Code in headless mode in each of the 30 worktrees,
# feeding each instance its corresponding prompt file.
#
# Usage: bash infra/scripts/launch-workers.sh [--dry-run] [--workers w01,w02,w03]
#
# Prerequisites:
#   - Claude Code CLI installed (`claude` command available)
#   - Worktrees created via create-worktrees.sh
#   - Prompt files exist in .claude/prompts/
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-worktrees"
PROMPTS_DIR="$PROJECT_ROOT/.claude/prompts"
LOG_DIR="$PROJECT_ROOT/infra/logs"
PID_DIR="$PROJECT_ROOT/infra/pids"

DRY_RUN=false
SPECIFIC_WORKERS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --workers) SPECIFIC_WORKERS="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Setup
mkdir -p "$LOG_DIR" "$PID_DIR"

echo "============================================"
echo " SelfPublisherForge — Launch Workers"
echo "============================================"
echo "Project root:  $PROJECT_ROOT"
echo "Worktrees:     $WORKTREE_BASE"
echo "Prompts:       $PROMPTS_DIR"
echo "Logs:          $LOG_DIR"
echo "Dry run:       $DRY_RUN"
echo ""

# Map worker IDs to prompt files
declare -A WORKER_PROMPTS=(
    [w01]="w01-project-scaffold.md"
    [w02]="w02-database-schema.md"
    [w03]="w03-auth-system.md"
    [w04]="w04-user-org-management.md"
    [w05]="w05-billing.md"
    [w06]="w06-file-storage.md"
    [w07]="w07-notifications.md"
    [w08]="w08-frontend-shell.md"
    [w09]="w09-api-gateway.md"
    [w10]="w10-websocket-realtime.md"
    [w11]="w11-task-queue.md"
    [w12]="w12-devops.md"
    [w13]="w13-market-intelligence.md"
    [w14]="w14-ai-writing.md"
    [w15]="w15-style-cloning.md"
    [w16]="w16-llm-orchestration.md"
    [w17]="w17-knowledge-vault.md"
    [w18]="w18-production-pipeline.md"
    [w19]="w19-publishing-ops.md"
    [w20]="w20-kdp-validation.md"
    [w21]="w21-product-page-lab.md"
    [w22]="w22-pricing-automation.md"
    [w23]="w23-competitor-finder.md"
    [w24]="w24-marketing.md"
    [w25]="w25-advertising.md"
    [w26]="w26-review-intelligence.md"
    [w27]="w27-analytics-bi.md"
    [w28]="w28-agent-system.md"
    [w29]="w29-portfolio-economics.md"
    [w30]="w30-chrome-ext-covers.md"
)

LAUNCHED=0
FAILED=0

# Determine which workers to launch
if [ -n "$SPECIFIC_WORKERS" ]; then
    IFS=',' read -ra WORKER_IDS <<< "$SPECIFIC_WORKERS"
else
    WORKER_IDS=($(for w in "${!WORKER_PROMPTS[@]}"; do echo "$w"; done | sort))
fi

for worker_id in "${WORKER_IDS[@]}"; do
    prompt_file="${WORKER_PROMPTS[$worker_id]}"
    worktree_dir="$WORKTREE_BASE/$worker_id"
    prompt_path="$PROMPTS_DIR/$prompt_file"
    log_file="$LOG_DIR/${worker_id}.log"
    pid_file="$PID_DIR/${worker_id}.pid"

    # Validate
    if [ ! -d "$worktree_dir" ]; then
        echo "  SKIP  $worker_id — worktree not found at $worktree_dir"
        FAILED=$((FAILED + 1))
        continue
    fi

    if [ ! -f "$prompt_path" ]; then
        echo "  SKIP  $worker_id — prompt not found at $prompt_path"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Read prompt content
    PROMPT_CONTENT=$(cat "$prompt_path")

    if [ "$DRY_RUN" = true ]; then
        echo "  DRY   $worker_id -> $worktree_dir (prompt: $prompt_file)"
        LAUNCHED=$((LAUNCHED + 1))
        continue
    fi

    echo "  LAUNCH $worker_id -> $worktree_dir"

    # Launch Claude Code in headless mode
    # --print flag outputs results, --dangerously-skip-permissions for autonomous operation
    (
        cd "$worktree_dir"
        claude --print \
            --dangerously-skip-permissions \
            --output-format text \
            "$PROMPT_CONTENT

IMPORTANT RULES:
- You are working in worktree: $worktree_dir
- You are on branch: $(cd "$worktree_dir" && git branch --show-current)
- Implement everything described in this prompt.
- Create all files listed.
- Write tests.
- Commit all changes with Conventional Commit messages.
- Do NOT modify shared read-only files listed in the prompt.
- When done, output a summary of what you implemented." \
            > "$log_file" 2>&1
    ) &

    echo $! > "$pid_file"
    echo "         PID: $(cat "$pid_file") | Log: $log_file"
    LAUNCHED=$((LAUNCHED + 1))

    # Small delay to avoid API rate limits
    sleep 2
done

echo ""
echo "============================================"
echo " Launched: $LAUNCHED | Failed: $FAILED"
echo "============================================"
echo ""
echo "Monitor progress:"
echo "  tail -f $LOG_DIR/w*.log"
echo ""
echo "Check status:"
echo "  bash infra/scripts/monitor-workers.sh"
echo ""
echo "Wait for all to complete:"
echo "  wait"
