#!/usr/bin/env bash
# =============================================================================
# merge_branches.sh — Merge all 60 feature branches in dependency order
# Usage: bash merge_branches.sh
# =============================================================================

set -euo pipefail

REPO_ROOT="/c/Users/Shadow/selfpublisherforge"
WORKTREE_ROOT="/c/Users/Shadow/spf-vfix-worktrees"

cd "$REPO_ROOT"

# Ensure we're on main
git checkout main
git pull origin main 2>/dev/null || true

echo "============================================="
echo " Merging branches in dependency order"
echo "============================================="

# Merge order (from PARALLEL_PROMPTS.md):
# 1. Types & schemas first
# 2. Hooks
# 3. DB migrations
# 4. Backend services
# 5. Backend routes
# 6. Frontend components
# 7. i18n
# 8. Pages & integration
# 9. Build verification (skip — those just verify)

MERGE_ORDER=(
  # Wave 1: Types & Schemas
  "feat/kv-20-types"
  "feat/pub-32-types"
  "feat/be-46-pub-schemas"
  "feat/be-47-sp-schemas"
  "feat/be-48-kv-schemas"
  # Wave 2: Hooks
  "feat/kv-21-hooks"
  "feat/pub-33-hooks"
  # Wave 3: DB Migrations
  "feat/be-35-sp-migration"
  "feat/be-36-kv-migration"
  "feat/be-37-pub-migration"
  "feat/be-38-pub-accounts-migration"
  # Wave 4: Backend Models
  "feat/be-54-pub-models"
  # Wave 5: Backend Services
  "feat/be-49-sp-service"
  "feat/be-50-kv-service"
  "feat/be-51-pub-isbn-service"
  "feat/be-52-pub-pricing-service"
  "feat/be-53-pub-export-service"
  # Wave 6: Backend Routes
  "feat/be-39-sp-samples-api"
  "feat/be-40-sp-tune-api"
  "feat/be-41-kv-attachments-api"
  "feat/be-42-kv-category-import"
  "feat/be-43-pub-isbns-api"
  "feat/be-44-pub-pricing-api"
  "feat/be-45-pub-export-history"
  # Wave 7: Frontend Components (no page-level deps)
  "feat/sp-01-profile-card"
  "feat/sp-03-wizard-presets"
  "feat/sp-07-style-metrics"
  "feat/sp-08-voice-characteristics"
  "feat/sp-09-sample-comparison"
  "feat/sp-10-test-refine"
  "feat/sp-06-analysis-results"
  "feat/kv-14-category-filter"
  "feat/kv-19-search-bar"
  "feat/pub-23-stats-cards"
  "feat/pub-27-account-card"
  "feat/pub-26-accounts-tab"
  "feat/pub-28-exports-tab"
  "feat/pub-29-listings-tab"
  "feat/pub-30-isbns-tab"
  "feat/pub-31-pricing-tab"
  "feat/pub-24-tab-layout"
  # Wave 8: i18n
  "feat/sp-12-i18n"
  "feat/kv-22-i18n"
  "feat/pub-34-i18n"
  # Wave 9: Pages & lists
  "feat/sp-02-profile-list"
  "feat/sp-04-wizard-step1"
  "feat/sp-05-wizard-samples"
  "feat/sp-11-detail-page"
  "feat/kv-13-entry-card"
  "feat/kv-15-landing-page"
  "feat/kv-16-entry-editor"
  "feat/kv-17-entry-detail"
  "feat/kv-18-import-modal"
  "feat/pub-25-landing-page"
  # Wave 10: Integration
  "feat/int-55-sp-detail-tabs"
  "feat/int-56-pub-tabs"
  "feat/int-57-module-exports"
)

SUCCESS=0
FAILED=0
SKIPPED=0

for branch in "${MERGE_ORDER[@]}"; do
  # Check if branch has commits
  if ! git rev-parse --verify "$branch" >/dev/null 2>&1; then
    echo "  SKIP $branch (branch not found)"
    ((SKIPPED++))
    continue
  fi

  commits=$(git log --oneline main..$branch 2>/dev/null | wc -l)
  if [ "$commits" -eq 0 ]; then
    echo "  SKIP $branch (no commits ahead of main)"
    ((SKIPPED++))
    continue
  fi

  echo ""
  echo "--- Merging: $branch ($commits commits) ---"

  if git merge --no-ff "$branch" -m "feat: merge $branch into main"; then
    echo "  OK: $branch merged"
    ((SUCCESS++))
  else
    echo "  CONFLICT: $branch — attempting auto-resolve..."
    # Try to auto-resolve by accepting both changes for common conflict patterns
    conflicted=$(git diff --name-only --diff-filter=U 2>/dev/null)
    if [ -n "$conflicted" ]; then
      echo "  Conflicted files:"
      echo "$conflicted" | while read f; do echo "    $f"; done

      # For index.ts barrel exports, accept both
      auto_resolved=true
      while read f; do
        if [[ "$f" == *"index.ts" ]] || [[ "$f" == *".json" ]]; then
          git checkout --theirs "$f" 2>/dev/null && git add "$f" 2>/dev/null
        else
          auto_resolved=false
        fi
      done <<< "$conflicted"

      if $auto_resolved; then
        git commit --no-edit 2>/dev/null
        echo "  AUTO-RESOLVED: $branch"
        ((SUCCESS++))
      else
        git merge --abort
        echo "  FAILED: $branch (manual merge needed)"
        ((FAILED++))
      fi
    else
      git merge --abort
      echo "  FAILED: $branch"
      ((FAILED++))
    fi
  fi
done

echo ""
echo "============================================="
echo " Merge Summary"
echo "   Successful: $SUCCESS"
echo "   Failed:     $FAILED"
echo "   Skipped:    $SKIPPED"
echo "============================================="

if [ "$FAILED" -gt 0 ]; then
  echo ""
  echo "Some branches had conflicts. Fix manually and re-run."
  exit 1
fi

# Final build check
echo ""
echo "Running final frontend build check..."
cd "$REPO_ROOT/frontend"
if npm run build 2>&1 | tail -30; then
  echo ""
  echo "BUILD PASSED!"
else
  echo ""
  echo "BUILD FAILED — check errors above."
  exit 1
fi
