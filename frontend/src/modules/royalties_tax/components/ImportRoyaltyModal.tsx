"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useImportRoyalty } from "../hooks";

interface ImportRoyaltyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const PLATFORMS = [
  {
    value: "kdp",
    label: "Amazon KDP",
    hint: "KDP Dashboard > Reports > Prior Months' Royalties",
  },
  {
    value: "ingram",
    label: "IngramSpark",
    hint: "IngramSpark > Compensation > Reports",
  },
  {
    value: "d2d",
    label: "Draft2Digital",
    hint: "D2D > Account > Payment History",
  },
  {
    value: "manual",
    label: "Manual Entry",
    hint: "Upload a custom CSV of manual royalty entries",
  },
];

export function ImportRoyaltyModal({ open, onOpenChange }: ImportRoyaltyModalProps) {
  const [platform, setPlatform] = useState<string>("kdp");
  const [file, setFile] = useState<File | null>(null);
  const importMutation = useImportRoyalty();

  const handleSubmit = async () => {
    if (!file) return;
    try {
      await importMutation.mutateAsync({ platform, file });
      setFile(null);
      onOpenChange(false);
    } catch {
      // Error rendered below
    }
  };

  const currentPlatform = PLATFORMS.find((p) => p.value === platform);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Import Royalty Data</DialogTitle>
          <DialogDescription>
            Import royalty data from your distribution platforms.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Platform</label>
            <div className="grid grid-cols-2 gap-2">
              {PLATFORMS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPlatform(p.value)}
                  className={`text-left rounded-md border px-3 py-2 text-sm transition-colors ${
                    platform === p.value
                      ? "border-blue-600 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="font-medium">{p.label}</div>
                </button>
              ))}
            </div>
            {currentPlatform && (
              <p className="mt-2 text-xs text-muted-foreground">
                Download from: {currentPlatform.hint}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">CSV / XLSX File</label>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-700
                         file:mr-3 file:py-2 file:px-3 file:rounded-md
                         file:border-0 file:bg-blue-600 file:text-white
                         file:text-sm file:font-medium hover:file:bg-blue-700"
            />
            {file && (
              <p className="mt-1 text-xs text-muted-foreground">
                Selected: {file.name} ({Math.round(file.size / 1024)} KB)
              </p>
            )}
          </div>

          {importMutation.isSuccess && importMutation.data && (
            <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800">
              Import complete — processed {importMutation.data.records_processed}
              {importMutation.data.records_failed > 0 &&
                `, failed ${importMutation.data.records_failed}`}
              .
            </div>
          )}

          {importMutation.isError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              Import failed: {importMutation.error.message}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!file || importMutation.isPending}
          >
            {importMutation.isPending ? "Importing..." : "Import"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
