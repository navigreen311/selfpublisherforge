"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  FileDown,
  CheckCircle2,
  XCircle,
  Loader2,
  Fingerprint,
} from "lucide-react";
import {
  useProvenance,
  useExportProvenance,
  type PageProvenance,
} from "../hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type ProvenanceStatus = PageProvenance["status"];

const STATUS_BADGE: Record<
  ProvenanceStatus,
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  verified: { label: "Verified", variant: "default" },
  pending: { label: "Pending", variant: "secondary" },
  missing: { label: "Missing", variant: "destructive" },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ProvenancePanelProps {
  bookId: string;
  bookType?: string;
}

export function ProvenancePanel({
  bookId,
  bookType = "childrens-books",
}: ProvenancePanelProps) {
  const { data, isLoading } = useProvenance(bookType, bookId);
  const exportMutation = useExportProvenance(bookType, bookId);

  const provenanceData = data?.pages ?? [];
  const fontData = data?.fonts ?? [];

  const handleExportReport = () => {
    exportMutation.mutate();
  };

  const formatDate = (iso: string) => {
    if (!iso) return "--";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">
              Provenance &amp; Compliance
            </h3>
            <p className="text-sm text-muted-foreground">
              Asset generation metadata and font licensing for legal protection.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleExportReport}
            disabled={exportMutation.isPending}
          >
            {exportMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileDown className="mr-2 h-4 w-4" />
            )}
            {exportMutation.isPending ? "Exporting..." : "Export Compliance Report"}
          </Button>
        </div>

        {/* Per-page Provenance Table */}
        <div>
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Fingerprint className="h-4 w-4" />
            Per-Page Provenance
          </h4>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Page #</TableHead>
                  <TableHead className="w-36">Model</TableHead>
                  <TableHead className="w-40">Prompt Hash</TableHead>
                  <TableHead className="w-28">Seed</TableHead>
                  <TableHead className="w-44">Generated Date</TableHead>
                  <TableHead className="w-24">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {provenanceData.map((row) => {
                  const badge = STATUS_BADGE[row.status];
                  return (
                    <TableRow key={row.page}>
                      <TableCell className="font-medium">{row.page}</TableCell>
                      <TableCell className="text-sm">
                        {row.model || "--"}
                      </TableCell>
                      <TableCell className="text-sm font-mono text-muted-foreground">
                        {row.promptHash || "--"}
                      </TableCell>
                      <TableCell className="text-sm font-mono">
                        {row.seed || "--"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {formatDate(row.generatedDate)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={badge.variant}>{badge.label}</Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>

        <Separator />

        {/* Font Licensing Table */}
        <div>
          <h4 className="text-sm font-semibold mb-3">Font Licensing</h4>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Font Name</TableHead>
                  <TableHead>License Type</TableHead>
                  <TableHead className="w-44 text-center">
                    Commercial Print Safe
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fontData.map((font) => (
                  <TableRow key={font.fontName}>
                    <TableCell className="font-medium">
                      {font.fontName}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {font.licenseType}
                    </TableCell>
                    <TableCell className="text-center">
                      {font.commercialPrintSafe ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600 mx-auto" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
