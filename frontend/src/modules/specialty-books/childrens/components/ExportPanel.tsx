"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  Download,
  FileCheck,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileDown,
  Tablet,
  Printer,
} from "lucide-react";
import { usePreflight, useExportBook } from "../hooks";
import type { PreflightResult } from "../types";

export interface ExportPanelProps {
  bookId: string;
}

const EXPORT_FORMATS = [
  { id: "print_pdf", label: "Print-Ready PDF", description: "KDP interior with bleed, trim, 300 DPI", icon: Printer },
  { id: "kpf", label: "Fixed-Layout KPF", description: "Kindle Package Format for tablets", icon: Tablet },
  { id: "epub", label: "Fixed-Layout EPUB", description: "For Apple Books and other platforms", icon: FileDown },
];

const STATUS_ICON = {
  pass: CheckCircle2,
  warn: AlertTriangle,
  fail: XCircle,
};

const STATUS_COLOR = {
  pass: "text-green-500",
  warn: "text-amber-500",
  fail: "text-destructive",
};

export function ExportPanel({ bookId }: ExportPanelProps) {
  const { mutate: runPreflight, isPending: isPreflighting } = usePreflight(bookId);
  const { mutate: exportBook, isPending: isExporting } = useExportBook(bookId);
  const [preflightResult, setPreflightResult] = useState<PreflightResult | null>(null);
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);

  const handlePreflight = () => {
    runPreflight(undefined, {
      onSuccess: (data) => setPreflightResult(data),
    });
  };

  const handleExport = (format: string) => {
    setExportingFormat(format);
    exportBook(
      { format },
      {
        onSuccess: (result) => {
          window.open(result.download_url, "_blank");
          setExportingFormat(null);
        },
        onError: () => setExportingFormat(null),
      },
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Download className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Export & Publish</span>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          {/* Preflight */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Preflight Check</h4>
              <Button size="sm" variant="outline" className="h-7 text-xs" onClick={handlePreflight} disabled={isPreflighting}>
                {isPreflighting ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <FileCheck className="h-3 w-3 mr-1" />}
                Run Check
              </Button>
            </div>

            {preflightResult && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {preflightResult.passed ? (
                    <Badge variant="secondary" className="text-green-600">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      All Passed
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      <XCircle className="h-3 w-3 mr-1" />
                      Issues Found
                    </Badge>
                  )}
                </div>
                {preflightResult.checks.map((check, i) => {
                  const Icon = STATUS_ICON[check.status];
                  return (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <Icon className={cn("h-3.5 w-3.5 mt-0.5 shrink-0", STATUS_COLOR[check.status])} />
                      <div>
                        <span className="font-medium">{check.name}</span>
                        <span className="text-muted-foreground ml-1">- {check.message}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Export formats */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Export Formats</h4>
            {EXPORT_FORMATS.map((fmt) => {
              const Icon = fmt.icon;
              const isBusy = isExporting && exportingFormat === fmt.id;
              return (
                <Card key={fmt.id}>
                  <CardContent className="pt-4 flex items-center gap-3">
                    <Icon className="h-5 w-5 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{fmt.label}</div>
                      <div className="text-xs text-muted-foreground">{fmt.description}</div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs shrink-0"
                      onClick={() => handleExport(fmt.id)}
                      disabled={isExporting}
                    >
                      {isBusy ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Download className="h-3 w-3 mr-1" />}
                      Export
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
