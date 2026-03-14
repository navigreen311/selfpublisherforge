cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-puzzle-wizard-step3-4

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify/complete Puzzle Steps 3 (Word Source radio, 13 Theme checkboxes, Seasonal toggle, Word Difficulty, Sanitization) and 4 (Answer Key layout, Book Extras checkboxes, Hint toggle, Clue Style, Layout 1/2 per page, Create button).

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify/complete Puzzle Steps 3 (Word Source radio, 13 Theme checkboxes, " && git push origin ai-feature/fix-puzzle-wizard-step3-4
