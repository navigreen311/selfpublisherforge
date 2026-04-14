"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useImportRoyalties } from "../hooks";

const DISTRIBUTORS = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram", label: "IngramSpark" },
  { value: "d2d", label: "Draft2Digital" },
];

export function RoyaltyImporterPanel() {
  const [distributor, setDistributor] = useState("kdp");
  const [file, setFile] = useState<File | null>(null);
  const importMut = useImportRoyalties();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    await importMut.mutateAsync({ file, distributor });
    setFile(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import Royalty Report</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <label className="block text-sm">
            Distributor
            <select
              value={distributor}
              onChange={(e) => setDistributor(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1"
            >
              {DISTRIBUTORS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            CSV File
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm"
            />
          </label>
          <Button
            type="submit"
            disabled={!file || importMut.isPending}
            size="sm"
          >
            {importMut.isPending ? "Importing..." : "Upload & Import"}
          </Button>
          <p className="text-xs text-muted-foreground">
            KDP: Dashboard &gt; Reports &gt; Prior Months&apos; Royalties.
            IngramSpark: Compensation &gt; Reports. D2D: Account &gt; Payment History.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
