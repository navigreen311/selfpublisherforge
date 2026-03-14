cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-childrens-bilingual

Read the relevant files first:
- frontend/src/app/(dashboard)/specialty/ for page files
- frontend/src/modules/specialty/ for hooks and components

Task: Verify Children's wizard Step 1 bilingual toggle. When ON, must show: Secondary Language dropdown (12 langs), Layout radio (Side-by-side/Alternating/Back section). If missing, add conditional rendering.

Read the existing file before making changes. Keep existing working code. Only add/fix what's described.

git add -A && git commit -m "fix: Verify Children's wizard Step 1 bilingual toggle. When ON, must show: Se" && git push origin ai-feature/fix-childrens-bilingual
