"use client";

import { useState } from "react";
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

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ProvenanceStatus = "verified" | "pending" | "missing";

interface PageProvenance {
  page: number;
  model: string;
  promptHash: string;
  seed: string;
  generatedDate: string;
  status: ProvenanceStatus;
}

interface FontLicenseEntry {
  fontName: string;
  licenseType: string;
  commercialPrintSafe: boolean;
}

const STATUS_BADGE: Record<
  ProvenanceStatus,
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  verified: { label: "Verified", variant: "default" },
  pending: { label: "Pending", variant: "secondary" },
  missing: { label: "Missing", variant: "destructive" },
};

// ---------------------------------------------------------------------------
// Mock data (will be replaced by API calls)
// ---------------------------------------------------------------------------

const MOCK_PROVENANCE: PageProvenance[] = [
  {
    page: 1,
    model: "DALL-E 3",
    promptHash: "a3f8c2d1e5b74f...",
    seed: "48291037",
    generatedDate: "2026-03-10T14:22:00Z",
    status: "verified",
  },
  {
    page: 2,
    model: "DALL-E 3",
    promptHash: "b7e1d4f9c2a836...",
    seed: "91720384",
    generatedDate: "2026-03-10T14:23:00Z",
    status: "verified",
  },
  {
    page: 3,
    model: "DALL-E 3",
    promptHash: "c9a2f3e8d1b647...",
    seed: "37461928",
    generatedDate: "2026-03-10T14:25:00Z",
    status: "verified",
  },
  {
    page: 4,
    model: "Stable Diffusion XL",
    promptHash: "d4b7c1e9f3a258...",
    seed: "62839140",
    generatedDate: "2026-03-11T09:12:00Z",
    status: "pending",
  },
  {
    page: 5,
    model: "",
    promptHash: "",
    seed: "",
    generatedDate: "",
    status: "missing",
  },
];

const MOCK_FONTS: FontLicenseEntry[] = [
  {
    fontName: "Open Sans",
    licenseType: "Apache 2.0",
    commercialPrintSafe: true,
  },
  {
    fontName: "Lora",
    licenseType: "OFL 1.1",
    commercialPrintSafe: true,
  },
  {
    fontName: "Comic Neue",
    licenseType: "OFL 1.1",
    commercialPrintSafe: true,
  },
  {
    fontName: "CustomHandwriting",
    licenseType: "Personal Use Only",
    commercialPrintSafe: false,
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ProvenancePanel() {
  const [exporting, setExporting] = useState(false);
  const [provenanceData] = useState<PageProvenance[]>(MOCK_PROVENANCE);
  const [fontData] = useState<FontLicenseEntry[]>(MOCK_FONTS);

  const handleExportReport = async () => {
    setExporting(true);
    // TODO: call API  GET /api/v1/specialty/childrens/{bookId}/provenance/export
    await new Promise((r) => setTimeout(r, 1500));
    // In production, this would trigger a PDF download
    setExporting(false);
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
            disabled={exporting}
          >
            {exporting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileDown className="mr-2 h-4 w-4" />
            )}
            {exporting ? "Exporting..." : "Export Compliance Report"}
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
