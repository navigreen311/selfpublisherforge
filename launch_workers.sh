#!/usr/bin/env bash
# =============================================================================
# launch_workers.sh — Dispatch 60 parallel Claude Code workers
# Usage: bash launch_workers.sh [start] [end]
#   e.g. bash launch_workers.sh          → runs all 60
#        bash launch_workers.sh 1 12     → runs workers 01-12 only
#        bash launch_workers.sh 35 48    → runs workers 35-48 only
# =============================================================================

set -euo pipefail

# Allow launching claude from within another claude session
unset CLAUDECODE 2>/dev/null || true

REPO_ROOT="/c/Users/Shadow/selfpublisherforge"
WORKTREE_ROOT="/c/Users/Shadow/spf-vfix-worktrees"
PROMPTS_FILE="$REPO_ROOT/PARALLEL_PROMPTS.md"
LOG_DIR="$REPO_ROOT/worker_logs"

START=${1:-1}
END=${2:-60}

mkdir -p "$LOG_DIR"

# Branch mapping
declare -A BRANCHES
BRANCHES[1]="feat/sp-01-profile-card"
BRANCHES[2]="feat/sp-02-profile-list"
BRANCHES[3]="feat/sp-03-wizard-presets"
BRANCHES[4]="feat/sp-04-wizard-step1"
BRANCHES[5]="feat/sp-05-wizard-samples"
BRANCHES[6]="feat/sp-06-analysis-results"
BRANCHES[7]="feat/sp-07-style-metrics"
BRANCHES[8]="feat/sp-08-voice-characteristics"
BRANCHES[9]="feat/sp-09-sample-comparison"
BRANCHES[10]="feat/sp-10-test-refine"
BRANCHES[11]="feat/sp-11-detail-page"
BRANCHES[12]="feat/sp-12-i18n"
BRANCHES[13]="feat/kv-13-entry-card"
BRANCHES[14]="feat/kv-14-category-filter"
BRANCHES[15]="feat/kv-15-landing-page"
BRANCHES[16]="feat/kv-16-entry-editor"
BRANCHES[17]="feat/kv-17-entry-detail"
BRANCHES[18]="feat/kv-18-import-modal"
BRANCHES[19]="feat/kv-19-search-bar"
BRANCHES[20]="feat/kv-20-types"
BRANCHES[21]="feat/kv-21-hooks"
BRANCHES[22]="feat/kv-22-i18n"
BRANCHES[23]="feat/pub-23-stats-cards"
BRANCHES[24]="feat/pub-24-tab-layout"
BRANCHES[25]="feat/pub-25-landing-page"
BRANCHES[26]="feat/pub-26-accounts-tab"
BRANCHES[27]="feat/pub-27-account-card"
BRANCHES[28]="feat/pub-28-exports-tab"
BRANCHES[29]="feat/pub-29-listings-tab"
BRANCHES[30]="feat/pub-30-isbns-tab"
BRANCHES[31]="feat/pub-31-pricing-tab"
BRANCHES[32]="feat/pub-32-types"
BRANCHES[33]="feat/pub-33-hooks"
BRANCHES[34]="feat/pub-34-i18n"
BRANCHES[35]="feat/be-35-sp-migration"
BRANCHES[36]="feat/be-36-kv-migration"
BRANCHES[37]="feat/be-37-pub-migration"
BRANCHES[38]="feat/be-38-pub-accounts-migration"
BRANCHES[39]="feat/be-39-sp-samples-api"
BRANCHES[40]="feat/be-40-sp-tune-api"
BRANCHES[41]="feat/be-41-kv-attachments-api"
BRANCHES[42]="feat/be-42-kv-category-import"
BRANCHES[43]="feat/be-43-pub-isbns-api"
BRANCHES[44]="feat/be-44-pub-pricing-api"
BRANCHES[45]="feat/be-45-pub-export-history"
BRANCHES[46]="feat/be-46-pub-schemas"
BRANCHES[47]="feat/be-47-sp-schemas"
BRANCHES[48]="feat/be-48-kv-schemas"
BRANCHES[49]="feat/be-49-sp-service"
BRANCHES[50]="feat/be-50-kv-service"
BRANCHES[51]="feat/be-51-pub-isbn-service"
BRANCHES[52]="feat/be-52-pub-pricing-service"
BRANCHES[53]="feat/be-53-pub-export-service"
BRANCHES[54]="feat/be-54-pub-models"
BRANCHES[55]="feat/int-55-sp-detail-tabs"
BRANCHES[56]="feat/int-56-pub-tabs"
BRANCHES[57]="feat/int-57-module-exports"
BRANCHES[58]="feat/test-58-sp-build"
BRANCHES[59]="feat/test-59-kv-build"
BRANCHES[60]="feat/test-60-pub-build"

# Extract prompt text for a given number (01-60) from PARALLEL_PROMPTS.md
extract_prompt() {
  local num=$1
  local padded=$(printf '%02d' $num)

  # Find the prompt section by PROMPT-XX header and extract until next PROMPT or section
  awk -v prompt="PROMPT-${padded}" '
    BEGIN { found=0; collecting=0 }
    $0 ~ "### " prompt ":" { found=1; collecting=1; next }
    collecting && /^### PROMPT-/ { collecting=0 }
    collecting && /^---$/ { collecting=0 }
    collecting && /^## [A-Z]/ { collecting=0 }
    collecting { print }
  ' "$PROMPTS_FILE" | sed '/^$/N;/^\n$/d' | sed 's/^[[:space:]]*//'
}

echo "============================================="
echo " Launching workers $START to $END"
echo " Logs: $LOG_DIR/"
echo "============================================="

PIDS=()

for i in $(seq $START $END); do
  padded=$(printf '%02d' $i)
  branch="${BRANCHES[$i]}"
  worktree="$WORKTREE_ROOT/fix${padded}"
  logfile="$LOG_DIR/worker-${padded}.log"

  if [ ! -d "$worktree" ]; then
    echo "SKIP worker $padded: worktree not found at $worktree"
    continue
  fi

  # Extract prompt
  prompt_text=$(extract_prompt $i)

  if [ -z "$prompt_text" ]; then
    echo "SKIP worker $padded: no prompt found"
    continue
  fi

  # Build the full instruction for the worker
  full_prompt="You are worker $padded working in a git worktree. Your branch is '$branch'.

IMPORTANT INSTRUCTIONS:
1. You are already in the correct worktree directory. All file paths in the prompt are relative to this repo root.
2. Make the changes described below.
3. After making changes, run the appropriate build check:
   - For frontend files: cd frontend && npx next build 2>&1 | tail -30
   - For backend .py files: python -c \"import ast; ast.parse(open('YOUR_FILE').read())\" to syntax check
   - For SQL files: just verify the file was created
4. Stage your changes with 'git add' (specific files only).
5. Commit with message: 'feat: <short description of what you did>'
6. Push: git push origin $branch

HERE IS YOUR TASK:
$prompt_text"

  echo "[$padded] Launching: $branch → $logfile"

  # Launch claude in headless mode in background
  (
    cd "$worktree"
    claude -p "$full_prompt" --allowedTools 'Bash(git commit:*),Bash(git add:*),Bash(git push:*),Bash(git status:*),Bash(npm run build:*),Bash(npx next build:*),Bash(python:*),Bash(cd:*),Bash(ls:*),Bash(mkdir:*),Read,Write,Edit,Glob,Grep' \
      > "$logfile" 2>&1
    echo "[$padded] DONE (exit=$?)" >> "$logfile"
  ) &

  PIDS+=($!)

  # Stagger launches by 2 seconds to avoid rate limiting
  sleep 2
done

echo ""
echo "============================================="
echo " All ${#PIDS[@]} workers launched!"
echo " Monitor with: tail -f $LOG_DIR/worker-*.log"
echo " Check status: for f in $LOG_DIR/worker-*.log; do echo \"\$f: \$(tail -1 \$f)\"; done"
echo "============================================="

# Wait for all to complete
echo ""
echo "Waiting for all workers to finish..."
for pid in "${PIDS[@]}"; do
  wait $pid 2>/dev/null || true
done

echo ""
echo "============================================="
echo " All workers complete!"
echo "============================================="

# Summary
echo ""
echo "Results:"
for i in $(seq $START $END); do
  padded=$(printf '%02d' $i)
  branch="${BRANCHES[$i]}"
  worktree="$WORKTREE_ROOT/fix${padded}"
  if [ -d "$worktree" ]; then
    commits=$(cd "$worktree" && git log --oneline main..HEAD 2>/dev/null | wc -l)
    if [ "$commits" -gt 0 ]; then
      echo "  [$padded] $branch: $commits commit(s)"
    else
      echo "  [$padded] $branch: NO COMMITS (check log)"
    fi
  fi
done
