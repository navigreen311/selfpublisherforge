cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-coloring-skeleton

Fix Coloring Books landing page. Read frontend/src/app/(dashboard)/specialty/coloring-books/page.tsx.

Two fixes: (1) Stat cards show skeleton bars instead of "0" — ensure the stats hook/fetch always resolves loading to false and renders 0 when no data. (2) Book grid stuck on skeletons — same fix as children's. When empty, show empty state with Palette icon, "No coloring books yet", create button to /specialty/coloring-books/new.

git add -A && git commit -m "fix: resolve Coloring Books skeleton loader bugs in stats and grid" && git push origin ai-feature/fix-coloring-skeleton
