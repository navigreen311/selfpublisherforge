#!/bin/bash
# ==============================================================================
# SelfPublisherForge — Monitor Worker Progress
# ==============================================================================
# Check status of all 30 Claude Code worker processes.
#
# Usage: bash infra/scripts/monitor-workers.sh [--watch]
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKTREE_BASE="$(dirname "$PROJECT_ROOT")/spf-worktrees"
LOG_DIR="$PROJECT_ROOT/infra/logs"
PID_DIR="$PROJECT_ROOT/infra/pids"

WATCH=false
[ "$1" = "--watch" ] && WATCH=true

show_status() {
    clear 2>/dev/null || true
    echo "============================================"
    echo " SelfPublisherForge — Worker Status"
    echo " $(date)"
    echo "============================================"
    echo ""

    RUNNING=0
    COMPLETED=0
    FAILED=0
    NOT_STARTED=0

    printf "%-6s %-40s %-10s %-8s %s\n" "ID" "BRANCH" "STATUS" "COMMITS" "LAST LOG LINE"
    printf "%-6s %-40s %-10s %-8s %s\n" "------" "----------------------------------------" "----------" "--------" "--------------------"

    for w in $(seq -w 1 30); do
        worker_id="w$w"
        pid_file="$PID_DIR/${worker_id}.pid"
        log_file="$LOG_DIR/${worker_id}.log"
        worktree_dir="$WORKTREE_BASE/$worker_id"

        # Get branch name
        branch=""
        if [ -d "$worktree_dir" ]; then
            branch=$(cd "$worktree_dir" && git branch --show-current 2>/dev/null || echo "?")
        fi

        # Get commit count
        commits=0
        if [ -d "$worktree_dir" ]; then
            commits=$(cd "$worktree_dir" && git rev-list --count HEAD ^$(git merge-base HEAD master 2>/dev/null || echo HEAD) 2>/dev/null || echo 0)
        fi

        # Determine status
        status="NOT_STARTED"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                status="RUNNING"
                RUNNING=$((RUNNING + 1))
            elif [ -f "$log_file" ]; then
                if grep -q "error\|Error\|ERROR\|failed\|Failed" "$log_file" 2>/dev/null; then
                    status="FAILED"
                    FAILED=$((FAILED + 1))
                else
                    status="COMPLETED"
                    COMPLETED=$((COMPLETED + 1))
                fi
            fi
        else
            NOT_STARTED=$((NOT_STARTED + 1))
        fi

        # Last log line
        last_line=""
        if [ -f "$log_file" ]; then
            last_line=$(tail -1 "$log_file" 2>/dev/null | cut -c1-50)
        fi

        # Color code status
        case $status in
            RUNNING)    printf "%-6s %-40s \033[33m%-10s\033[0m %-8s %s\n" "$worker_id" "$branch" "$status" "$commits" "$last_line" ;;
            COMPLETED)  printf "%-6s %-40s \033[32m%-10s\033[0m %-8s %s\n" "$worker_id" "$branch" "$status" "$commits" "$last_line" ;;
            FAILED)     printf "%-6s %-40s \033[31m%-10s\033[0m %-8s %s\n" "$worker_id" "$branch" "$status" "$commits" "$last_line" ;;
            *)          printf "%-6s %-40s %-10s %-8s %s\n" "$worker_id" "$branch" "$status" "$commits" "$last_line" ;;
        esac
    done

    echo ""
    echo "============================================"
    printf " Running: %d | Completed: %d | Failed: %d | Not Started: %d\n" $RUNNING $COMPLETED $FAILED $NOT_STARTED
    echo "============================================"
}

if [ "$WATCH" = true ]; then
    while true; do
        show_status
        sleep 10
    done
else
    show_status
fi
