cd /c/Users/Shadow/selfpublisherforge && git checkout main && git pull origin main && git checkout -b ai-feature/fix-shared-filter-bar

Create a reusable FilterBar component. First read frontend/src/app/(dashboard)/specialty/childrens-books/page.tsx for existing patterns.

Create frontend/src/modules/specialty/shared/components/FilterBar.tsx with: search input (with placeholder), status Select (All Statuses/Draft/In Progress/Published), sort Select (Recently Updated/Title A-Z/Title Z-A/Date Created/QA Score). Use shadcn/ui Input and Select components. Props: searchPlaceholder, searchValue, onSearchChange, statusValue, onStatusChange, sortValue, onSortChange. Layout: flex row with gap-3, search takes flex-1.

git add -A && git commit -m "feat: add reusable FilterBar component with search, status, and sort" && git push origin ai-feature/fix-shared-filter-bar
