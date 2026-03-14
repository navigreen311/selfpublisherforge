"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  BookOpen,
  Mail,
  Star,
  User,
  QrCode,
  Plus,
  Eye,
  Library,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BackMatterType =
  | "also_in_series"
  | "about_series"
  | "email_cta"
  | "review_request"
  | "about_author";

export interface AuthorInfo {
  name: string;
  bio: string;
  photoUrl?: string;
  website?: string;
  social?: Record<string, string>;
}

export interface BackMatterPage {
  type: BackMatterType;
  title: string;
  htmlContent: string;
  assets: Record<string, string>;
}

export interface BackMatterEditorProps {
  seriesId: string | null;
  seriesName: string;
  currentBookId: string;
  authorInfo: AuthorInfo;
  onAuthorInfoChange: (info: AuthorInfo) => void;
  onGenerate: (type: BackMatterType, options: Record<string, string>) => void;
  onAddToBook: (page: BackMatterPage) => void;
  onGenerateQrCode: (url: string) => void;
  generatedPages: BackMatterPage[];
  qrCodeData: string | null;
  isGenerating: boolean;
}

// ---------------------------------------------------------------------------
// Template type config
// ---------------------------------------------------------------------------

const TEMPLATE_TYPES: {
  value: BackMatterType;
  label: string;
  description: string;
  icon: React.ElementType;
}[] = [
  {
    value: "also_in_series",
    label: "Also in Series",
    description: "Showcase other volumes with cover thumbnails and links.",
    icon: Library,
  },
  {
    value: "about_series",
    label: "About Series",
    description: "Series description and available volume count.",
    icon: BookOpen,
  },
  {
    value: "email_cta",
    label: "Email CTA",
    description: "Email signup call-to-action with QR code.",
    icon: Mail,
  },
  {
    value: "review_request",
    label: "Review Request",
    description: "Friendly request for an Amazon review.",
    icon: Star,
  },
  {
    value: "about_author",
    label: "About Author",
    description: "Author bio, photo, and social links.",
    icon: User,
  },
];

// ---------------------------------------------------------------------------
// Template editors per type
// ---------------------------------------------------------------------------

function AlsoInSeriesEditor({
  seriesName,
  onGenerate,
}: {
  seriesName: string;
  onGenerate: () => void;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Generates a page listing all other volumes in the{" "}
        <strong>{seriesName || "series"}</strong> with cover thumbnails.
      </p>
      <Button size="sm" onClick={onGenerate}>
        Generate Page
      </Button>
    </div>
  );
}

function AboutSeriesEditor({
  seriesName,
  onGenerate,
}: {
  seriesName: string;
  onGenerate: () => void;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Generates a description page for the <strong>{seriesName || "series"}</strong> with
        volume count and overview.
      </p>
      <Button size="sm" onClick={onGenerate}>
        Generate Page
      </Button>
    </div>
  );
}

function EmailCtaEditor({
  onGenerate,
  onGenerateQr,
  qrCodeData,
}: {
  onGenerate: (url: string) => void;
  onGenerateQr: (url: string) => void;
  qrCodeData: string | null;
}) {
  const [ctaUrl, setCtaUrl] = React.useState("");

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="cta-url">Signup URL</Label>
        <Input
          id="cta-url"
          type="url"
          value={ctaUrl}
          onChange={(e) => setCtaUrl(e.target.value)}
          placeholder="https://example.com/newsletter"
        />
      </div>

      <div className="flex gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onGenerateQr(ctaUrl)}
          disabled={!ctaUrl.trim()}
        >
          <QrCode className="mr-1 h-3 w-3" />
          Preview QR Code
        </Button>
        <Button size="sm" onClick={() => onGenerate(ctaUrl)} disabled={!ctaUrl.trim()}>
          Generate Page
        </Button>
      </div>

      {qrCodeData && (
        <Card className="flex items-center justify-center p-4">
          <img
            src={`data:image/png;base64,${qrCodeData}`}
            alt="QR Code preview"
            className="h-32 w-32"
          />
        </Card>
      )}
    </div>
  );
}

function ReviewRequestEditor({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Generates a friendly, non-pushy page asking readers to leave an Amazon review.
        Uses KDP best-practice wording.
      </p>
      <Button size="sm" onClick={onGenerate}>
        Generate Page
      </Button>
    </div>
  );
}

function AboutAuthorEditor({
  authorInfo,
  onAuthorInfoChange,
  onGenerate,
}: {
  authorInfo: AuthorInfo;
  onAuthorInfoChange: (info: AuthorInfo) => void;
  onGenerate: () => void;
}) {
  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="author-name">Name</Label>
        <Input
          id="author-name"
          value={authorInfo.name}
          onChange={(e) => onAuthorInfoChange({ ...authorInfo, name: e.target.value })}
          placeholder="Author name"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="author-bio">Bio</Label>
        <Textarea
          id="author-bio"
          value={authorInfo.bio}
          onChange={(e) => onAuthorInfoChange({ ...authorInfo, bio: e.target.value })}
          placeholder="Tell readers about yourself..."
          rows={4}
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="author-photo">Photo URL</Label>
        <Input
          id="author-photo"
          value={authorInfo.photoUrl || ""}
          onChange={(e) =>
            onAuthorInfoChange({ ...authorInfo, photoUrl: e.target.value || undefined })
          }
          placeholder="https://example.com/photo.jpg"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="author-website">Website</Label>
        <Input
          id="author-website"
          value={authorInfo.website || ""}
          onChange={(e) =>
            onAuthorInfoChange({ ...authorInfo, website: e.target.value || undefined })
          }
          placeholder="https://example.com"
        />
      </div>
      <Button size="sm" onClick={onGenerate}>
        Generate Page
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preview panel
// ---------------------------------------------------------------------------

function PagePreview({ page }: { page: BackMatterPage }) {
  return (
    <Card className="space-y-2 p-4">
      <div className="flex items-center gap-2">
        <Eye className="h-4 w-4 text-muted-foreground" />
        <p className="text-sm font-medium">{page.title}</p>
      </div>
      <div
        className="prose prose-sm max-h-64 overflow-y-auto rounded border bg-white p-3 text-xs dark:bg-gray-950"
        dangerouslySetInnerHTML={{ __html: page.htmlContent }}
      />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function BackMatterEditor({
  seriesId,
  seriesName,
  currentBookId,
  authorInfo,
  onAuthorInfoChange,
  onGenerate,
  onAddToBook,
  onGenerateQrCode,
  generatedPages,
  qrCodeData,
  isGenerating,
}: BackMatterEditorProps) {
  const [selectedType, setSelectedType] = React.useState<BackMatterType>("also_in_series");

  const currentTemplate = TEMPLATE_TYPES.find((t) => t.value === selectedType)!;

  const handleGenerate = (options: Record<string, string> = {}) => {
    onGenerate(selectedType, options);
  };

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Template type selector                                            */}
      {/* ----------------------------------------------------------------- */}
      <div className="space-y-2">
        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Back Matter Template
        </Label>
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
          {TEMPLATE_TYPES.map((tmpl) => {
            const Icon = tmpl.icon;
            return (
              <Card
                key={tmpl.value}
                className={cn(
                  "flex cursor-pointer flex-col items-center gap-1 p-3 text-center transition-colors hover:bg-muted/50",
                  selectedType === tmpl.value && "border-primary bg-muted/30",
                )}
                onClick={() => setSelectedType(tmpl.value)}
              >
                <Icon className="h-5 w-5" />
                <p className="text-xs font-medium">{tmpl.label}</p>
              </Card>
            );
          })}
        </div>
        <p className="text-xs text-muted-foreground">{currentTemplate.description}</p>
      </div>

      <Separator />

      {/* ----------------------------------------------------------------- */}
      {/* Editor per type                                                   */}
      {/* ----------------------------------------------------------------- */}
      <div>
        {selectedType === "also_in_series" && (
          <AlsoInSeriesEditor seriesName={seriesName} onGenerate={() => handleGenerate()} />
        )}
        {selectedType === "about_series" && (
          <AboutSeriesEditor seriesName={seriesName} onGenerate={() => handleGenerate()} />
        )}
        {selectedType === "email_cta" && (
          <EmailCtaEditor
            onGenerate={(url) => handleGenerate({ cta_url: url })}
            onGenerateQr={onGenerateQrCode}
            qrCodeData={qrCodeData}
          />
        )}
        {selectedType === "review_request" && (
          <ReviewRequestEditor onGenerate={() => handleGenerate()} />
        )}
        {selectedType === "about_author" && (
          <AboutAuthorEditor
            authorInfo={authorInfo}
            onAuthorInfoChange={onAuthorInfoChange}
            onGenerate={() => handleGenerate()}
          />
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Generated pages preview                                           */}
      {/* ----------------------------------------------------------------- */}
      {generatedPages.length > 0 && (
        <>
          <Separator />
          <div className="space-y-3">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Generated Pages
            </Label>
            {generatedPages.map((page, idx) => (
              <div key={idx} className="space-y-2">
                <PagePreview page={page} />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onAddToBook(page)}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  Add to Book
                </Button>
              </div>
            ))}
          </div>
        </>
      )}

      {isGenerating && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          Generating back matter page...
        </div>
      )}
    </div>
  );
}
