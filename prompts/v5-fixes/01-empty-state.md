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
