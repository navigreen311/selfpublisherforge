cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-childrens-filters

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Fix Children's Books filter dropdowns: read the landing page, replace empty/unlabeled dropdowns with properly labeled Select components. Status filter: All/Draft/In Progress/Published. Sort: Recently Updated/Title A-Z/Z-A/Date Created/QA Score. Wire up filtering logic.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Fix Children's Books filter dropdowns: read the landing page, replace em" && git push origin ai-feature/fix-childrens-filters
