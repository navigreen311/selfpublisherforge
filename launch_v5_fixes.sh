#!/bin/bash
# Launch 20 parallel Claude Code agents for v5 fixes
# Run from repo root: cd ~/selfpublisherforge && bash launch_v5_fixes.sh
set -e
cd "$(dirname "$0")"

LOG_DIR="worker_logs_v5"
PROMPT_DIR="prompts/v5-fixes"
mkdir -p "$LOG_DIR" "$PROMPT_DIR"

# Helper to launch an agent
launch() {
  local name="$1"
  local prompt_file="$PROMPT_DIR/${name}.md"
  echo "  Launching: $name"
  claude -p "$(cat "$prompt_file")" --output-format text --dangerously-skip-permissions > "$LOG_DIR/${name}.log" 2>&1 &
}

echo "Creating prompt files..."

# === 01: Shared EmptyState ===
cat > "$PROMPT_DIR/01-empty-state.md" << 'PROMPT'
cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-shared-empty-state

Create a reusable EmptyState component. First read frontend/src/app/(dashboard)/specialty/childrens-books/page.tsx to understand existing patterns.

Create frontend/src/modules/specialty/shared/components/EmptyState.tsx:

"use client";
import { Button } from "@/components/ui/button";
import { type LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 border-2 border-dashed border-muted rounded-xl">
      <div className="rounded-full bg-muted p-4 mb-4"><Icon className="h-10 w-10 text-muted-foreground" /></div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground text-center max-w-md mb-6">{description}</p>
      <Button onClick={onAction}>{actionLabel}</Button>
    </div>
  );
}

git add -A && git commit -m "feat: add reusable EmptyState component for specialty book landing pages" && git push origin ai-feature/fix-shared-empty-state
PROMPT

# === 02: Shared FilterBar ===
cat > "$PROMPT_DIR/02-filter-bar.md" << 'PROMPT'
cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-shared-filter-bar

Create a reusable FilterBar component. First read frontend/src/app/(dashboard)/specialty/childrens-books/page.tsx for existing patterns.

Create frontend/src/modules/specialty/shared/components/FilterBar.tsx with: search input (with placeholder), status Select (All Statuses/Draft/In Progress/Published), sort Select (Recently Updated/Title A-Z/Title Z-A/Date Created/QA Score). Use shadcn/ui Input and Select components. Props: searchPlaceholder, searchValue, onSearchChange, statusValue, onStatusChange, sortValue, onSortChange. Layout: flex row with gap-3, search takes flex-1.

git add -A && git commit -m "feat: add reusable FilterBar component with search, status, and sort" && git push origin ai-feature/fix-shared-filter-bar
PROMPT

# === 03: Children's skeleton fix ===
cat > "$PROMPT_DIR/03-childrens-skeleton.md" << 'PROMPT'
cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-childrens-skeleton

Fix the Children's Books landing page skeleton loader bug. Read frontend/src/app/(dashboard)/specialty/childrens-books/page.tsx.

The bug: loading state stays true when API returns empty data. Fix the loading pattern so loading is ALWAYS set to false after fetch (success or error). When items are empty show an empty state with BookOpen icon, "No children's books yet", "Create your first illustrated children's book with AI-generated artwork.", and a create button linking to /specialty/childrens-books/new.

The render pattern should be: loading ? <Skeleton> : error ? <Error> : items.length === 0 ? <EmptyState> : <Grid>

Also check the hooks file for this module and fix the loading state there if the data fetching happens in a hook.

git add -A && git commit -m "fix: resolve Children's Books skeleton loader bug, add empty state" && git push origin ai-feature/fix-childrens-skeleton
PROMPT

# === 04: Coloring skeleton fix ===
cat > "$PROMPT_DIR/04-coloring-skeleton.md" << 'PROMPT'
cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-coloring-skeleton

Fix Coloring Books landing page. Read frontend/src/app/(dashboard)/specialty/coloring-books/page.tsx.

Two fixes: (1) Stat cards show skeleton bars instead of "0" — ensure the stats hook/fetch always resolves loading to false and renders 0 when no data. (2) Book grid stuck on skeletons — same fix as children's. When empty, show empty state with Palette icon, "No coloring books yet", create button to /specialty/coloring-books/new.

git add -A && git commit -m "fix: resolve Coloring Books skeleton loader bugs in stats and grid" && git push origin ai-feature/fix-coloring-skeleton
PROMPT

# === 05-20: Create remaining prompts ===
for i in $(seq 5 20); do
  case $i in
    5) name="05-puzzle-verify"; branch="fix-puzzle-verify"; msg="Fix Puzzle Books: verify skeleton works, change Kids age '4-8' to '5-10' in all puzzle files. Search and replace across page.tsx, new/page.tsx, types, hooks.";;
    6) name="06-childrens-filters"; branch="fix-childrens-filters"; msg="Fix Children's Books filter dropdowns: read the landing page, replace empty/unlabeled dropdowns with properly labeled Select components. Status filter: All/Draft/In Progress/Published. Sort: Recently Updated/Title A-Z/Z-A/Date Created/QA Score. Wire up filtering logic.";;
    7) name="07-coloring-filters"; branch="fix-coloring-filters"; msg="Add/fix filter bar on Coloring Books landing page. If missing, add search + status dropdown + sort dropdown. Wire up filtering.";;
    8) name="08-puzzle-filters"; branch="fix-puzzle-filters"; msg="Add/fix filter bar on Puzzle Books landing page. If missing, add search + status dropdown + sort dropdown. Wire up filtering.";;
    9) name="09-childrens-wizard-step2"; branch="fix-childrens-wizard-step2"; msg="Verify/complete Children's wizard Step 2 (Format & Style). Must have: Page Count dropdown, Trim Size dropdown (8.5x8.5/8.5x11/10x8/6x9), 8 Illustration Style cards (Watercolor/Cartoon/Flat/Storybook/Realistic/Crayon/Collage/Anime), Color Palette dropdown, Style Clone option. Read the wizard file first.";;
    10) name="10-childrens-wizard-step3-4"; branch="fix-childrens-wizard-step3-4"; msg="Verify/complete Children's wizard Steps 3 (Story Setup: Creation Mode radio, Story Prompt, Theme, Character, Setting, Tone, Story Mode) and 4 (Content Safety: Fear Intensity, 5 Content Exclusion checkboxes, 3 Illustration Safety checkboxes, Create Book button).";;
    11) name="11-childrens-bilingual"; branch="fix-childrens-bilingual"; msg="Verify Children's wizard Step 1 bilingual toggle. When ON, must show: Secondary Language dropdown (12 langs), Layout radio (Side-by-side/Alternating/Back section). If missing, add conditional rendering.";;
    12) name="12-coloring-wizard"; branch="fix-coloring-wizard-steps"; msg="Verify/complete Coloring wizard Steps 2 (Page Count/Trim/6 Line Art styles/Line Weight/Uniformity/Complexity/Page Options) and 3 (Theme/Generation Method/Include checkboxes: title page, belongs-to, color test, progress tracker, certificate, difficulty).";;
    13) name="13-coloring-series"; branch="fix-coloring-series"; msg="Verify Coloring wizard Step 1 series toggle. When ON, must show Series Name input and Volume Number dropdown. If missing, add.";;
    14) name="14-puzzle-wizard-step2"; branch="fix-puzzle-wizard-step2"; msg="Verify/complete Puzzle wizard Step 2. Must have: multi-select puzzle type table (Word Search/Crossword/Maze/Sudoku/Word Scramble/Cryptogram/Number Search/Word Connect/Trivia) with quantity/difficulty/grid size per type. Difficulty mode: Progressive/Fixed/Mixed. Total count display.";;
    15) name="15-puzzle-wizard-step3-4"; branch="fix-puzzle-wizard-step3-4"; msg="Verify/complete Puzzle Steps 3 (Word Source radio, 13 Theme checkboxes, Seasonal toggle, Word Difficulty, Sanitization) and 4 (Answer Key layout, Book Extras checkboxes, Hint toggle, Clue Style, Layout 1/2 per page, Create button).";;
    16) name="16-puzzle-ai-suggest"; branch="fix-puzzle-ai-suggest"; msg="Verify/implement AI Suggest button for Puzzle subtitle. Generate subtitle from title+types+difficulty using template: '{count} {types} Puzzles with Answers — {difficulty}'. If button does nothing, implement it.";;
    17) name="17-template-prefill"; branch="fix-template-prefill"; msg="Verify all Use Template buttons on Coloring (8 templates) and Puzzle (8 templates) landing pages pre-fill the wizard. Templates should navigate to /new?template=NAME and wizard reads query param to pre-fill. Fix if broken.";;
    18) name="18-childrens-editor"; branch="fix-childrens-editor"; msg="Verify/enhance Children's Books editor at [id]/page.tsx. Must have: left panel (page thumbnails), center (two-page spread), right panel (layout selector 7 options, text editor, illustration prompt, generate/upload buttons, character toggle). If placeholder, build it out.";;
    19) name="19-coloring-editor"; branch="fix-coloring-editor"; msg="Verify/enhance Coloring Books editor at [id]/page.tsx. Must have: left panel (page thumbnails), center (page preview), right panel (illustration prompt, generate/upload, quality pipeline, post-processing controls, simulation preview, border/difficulty/caption).";;
    20) name="20-puzzle-editor"; branch="fix-puzzle-editor"; msg="Verify/enhance Puzzle Books editor at [id]/page.tsx. Must have: left panel (page thumbnails with difficulty badges), center (puzzle preview), right panel (theme, grid size, difficulty, direction toggles, word list editor, regenerate, answer key toggle).";;
  esac

  cat > "$PROMPT_DIR/${name}.md" << EOF
cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/${branch}

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: ${msg}

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: ${msg:0:72}" && git push origin ai-feature/${branch}
EOF
done

echo ""
echo "Launching 20 agents..."
for f in "$PROMPT_DIR"/*.md; do
  launch "$(basename "$f" .md)"
done

echo ""
echo "All 20 agents launched!"
echo "Monitor: tail -f $LOG_DIR/*.log"
echo ""
wait
echo "All agents completed!"
