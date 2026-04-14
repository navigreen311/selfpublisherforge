"use client";

import { PenNamesList } from "@/modules/pen-names/components/PenNamesList";
import { Separator } from "@/components/ui/separator";

export default function PenNamesSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Pen Names</h2>
        <p className="text-sm text-muted-foreground">
          Self-publishers often use several author identities across genres.
          Manage each identity’s bio, Amazon author page, and primary genres
          here.
        </p>
      </div>
      <Separator />
      <PenNamesList />
    </div>
  );
}
