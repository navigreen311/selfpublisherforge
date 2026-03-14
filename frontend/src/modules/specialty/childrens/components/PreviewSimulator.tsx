"use client";

import { useState, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  ChevronLeft,
  ChevronRight,
  Smartphone,
  Monitor,
  Layers,
  Eye,
  BookOpen,
  FileText,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PageData {
  number: number;
  imageUrl: string | null;
  text: string;
}

interface HookScoreBreakdown {
  coverAppeal: number;
  openingText: number;
  illustrationQuality: number;
  pageTurnMomentum: number;
  overallHook: number;
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_PAGES: PageData[] = Array.from({ length: 24 }, (_, i) => ({
  number: i + 1,
  imageUrl: null,
  text: i === 0 ? "Once upon a time..." : `Page ${i + 1} content`,
}));

const MOCK_HOOK_SCORE: HookScoreBreakdown = {
  coverAppeal: 82,
  openingText: 75,
  illustrationQuality: 88,
  pageTurnMomentum: 70,
  overallHook: 79,
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PagePlaceholder({ page }: { page: PageData }) {
  return (
    <div className="bg-white border rounded shadow-sm flex flex-col items-center justify-center aspect-[3/4] relative">
      <div className="absolute inset-0 bg-muted/20" />
      {page.imageUrl ? (
        <img
          src={page.imageUrl}
          alt={`Page ${page.number}`}
          className="object-contain w-full h-full"
        />
      ) : (
        <div className="flex flex-col items-center gap-2 text-muted-foreground p-4">
          <FileText className="h-8 w-8 opacity-40" />
          <span className="text-xs text-center">{page.text}</span>
        </div>
      )}
      <span className="absolute bottom-1 right-2 text-[10px] text-muted-foreground">
        {page.number}
      </span>
    </div>
  );
}

function GuideOverlays() {
  return (
    <>
      {/* Bleed zone */}
      <div className="absolute inset-0 border-2 border-dashed border-red-300/50 pointer-events-none" />
      {/* Trim line */}
      <div className="absolute inset-[4px] border border-blue-400/40 pointer-events-none" />
      {/* Safe zone */}
      <div className="absolute inset-[12px] border border-green-400/40 pointer-events-none" />
      {/* Gutter zone (center) */}
      <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-4 bg-yellow-300/10 border-x border-yellow-400/30 pointer-events-none" />
    </>
  );
}

function HookScoreDisplay({ score }: { score: HookScoreBreakdown }) {
  const color =
    score.overallHook >= 80
      ? "text-green-600"
      : score.overallHook >= 60
        ? "text-yellow-600"
        : "text-red-600";

  const breakdown = [
    { label: "Cover Appeal", value: score.coverAppeal },
    { label: "Opening Text", value: score.openingText },
    { label: "Illustration Quality", value: score.illustrationQuality },
    { label: "Page-Turn Momentum", value: score.pageTurnMomentum },
  ];

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-3 mb-3">
        <Eye className="h-5 w-5 text-muted-foreground" />
        <span className="text-sm font-semibold">Hook Score</span>
        <span className={`text-2xl font-bold ml-auto ${color}`}>
          {score.overallHook}
        </span>
        <span className="text-xs text-muted-foreground">/100</span>
      </div>
      <div className="space-y-2">
        {breakdown.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-36">
              {item.label}
            </span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${item.value}%` }}
              />
            </div>
            <span className="text-xs font-medium w-8 text-right">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function PreviewSimulator() {
  const [currentPage, setCurrentPage] = useState(0);
  const [showGuides, setShowGuides] = useState(false);
  const [pages] = useState<PageData[]>(MOCK_PAGES);
  const [hookScore] = useState<HookScoreBreakdown>(MOCK_HOOK_SCORE);

  const totalPages = pages.length;

  // Look Inside shows first 10%
  const lookInsidePages = useMemo(() => {
    const count = Math.max(1, Math.ceil(totalPages * 0.1));
    return pages.slice(0, count);
  }, [pages, totalPages]);

  const canGoBack = currentPage > 0;
  const canGoForward = currentPage < totalPages - 2; // spread = 2 pages

  const goBack = () => setCurrentPage((p) => Math.max(0, p - 2));
  const goForward = () =>
    setCurrentPage((p) => Math.min(totalPages - 2, p + 2));

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Preview Simulator</h3>
          <div className="flex items-center gap-3">
            <Switch
              id="guide-toggle"
              checked={showGuides}
              onCheckedChange={setShowGuides}
            />
            <Label htmlFor="guide-toggle" className="text-sm cursor-pointer">
              Guide Overlays
            </Label>
          </div>
        </div>

        <Tabs defaultValue="spread">
          <TabsList>
            <TabsTrigger value="spread">
              <BookOpen className="h-4 w-4 mr-1.5" />
              Spread View
            </TabsTrigger>
            <TabsTrigger value="single">
              <FileText className="h-4 w-4 mr-1.5" />
              Single Page
            </TabsTrigger>
            <TabsTrigger value="lookinside">
              <Layers className="h-4 w-4 mr-1.5" />
              Look Inside
            </TabsTrigger>
          </TabsList>

          {/* ---- Spread View ---- */}
          <TabsContent value="spread">
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-full max-w-3xl">
                <div className="grid grid-cols-2 gap-1 bg-muted/30 p-4 rounded-lg">
                  {pages[currentPage] && (
                    <PagePlaceholder page={pages[currentPage]} />
                  )}
                  {pages[currentPage + 1] && (
                    <PagePlaceholder page={pages[currentPage + 1]} />
                  )}
                </div>
                {showGuides && <GuideOverlays />}
              </div>

              {/* Navigation */}
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={goBack}
                  disabled={!canGoBack}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  Pages {currentPage + 1}-
                  {Math.min(currentPage + 2, totalPages)} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={goForward}
                  disabled={!canGoForward}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* ---- Single Page ---- */}
          <TabsContent value="single">
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-full max-w-md mx-auto">
                {pages[currentPage] && (
                  <PagePlaceholder page={pages[currentPage]} />
                )}
                {showGuides && <GuideOverlays />}
              </div>

              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.max(0, p - 1))
                  }
                  disabled={currentPage <= 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {currentPage + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages - 1, p + 1))
                  }
                  disabled={currentPage >= totalPages - 1}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* ---- Look Inside Simulator ---- */}
          <TabsContent value="lookinside">
            <div className="space-y-6">
              <p className="text-sm text-muted-foreground">
                Simulates what Amazon shoppers see in the &quot;Look
                Inside&quot; preview (first 10% of pages).
              </p>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Phone frame (375px) */}
                <div className="flex flex-col items-center gap-2">
                  <div className="flex items-center gap-1 text-sm font-medium text-muted-foreground">
                    <Smartphone className="h-4 w-4" />
                    Mobile (375px)
                  </div>
                  <div className="border-4 border-gray-800 rounded-[2rem] p-2 bg-black w-[220px]">
                    <div className="bg-white rounded-xl overflow-hidden">
                      <div className="bg-muted/50 px-2 py-1 border-b">
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full bg-gray-300" />
                          <div className="flex-1 h-2 bg-gray-200 rounded" />
                        </div>
                      </div>
                      <div className="p-2 space-y-2" style={{ minHeight: 320 }}>
                        <Badge variant="secondary" className="text-[8px]">
                          Look Inside
                        </Badge>
                        {lookInsidePages.map((page) => (
                          <div
                            key={page.number}
                            className="bg-muted/20 border rounded p-2 text-[9px] text-muted-foreground text-center"
                          >
                            <div className="aspect-[3/4] bg-muted/30 rounded mb-1 flex items-center justify-center">
                              <FileText className="h-4 w-4 opacity-30" />
                            </div>
                            p.{page.number}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Desktop frame (1024px) */}
                <div className="flex flex-col items-center gap-2">
                  <div className="flex items-center gap-1 text-sm font-medium text-muted-foreground">
                    <Monitor className="h-4 w-4" />
                    Desktop (1024px)
                  </div>
                  <div className="border-2 border-gray-700 rounded-lg bg-white w-full max-w-md overflow-hidden">
                    <div className="bg-gray-100 px-3 py-1.5 border-b flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-400" />
                        <div className="w-2 h-2 rounded-full bg-yellow-400" />
                        <div className="w-2 h-2 rounded-full bg-green-400" />
                      </div>
                      <div className="flex-1 h-3 bg-gray-200 rounded text-[8px] text-muted-foreground flex items-center px-2">
                        amazon.com/dp/...
                      </div>
                    </div>
                    <div className="p-4 space-y-3" style={{ minHeight: 280 }}>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px]">
                          Look Inside
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          First {lookInsidePages.length} page
                          {lookInsidePages.length !== 1 ? "s" : ""} preview
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        {lookInsidePages.map((page) => (
                          <div
                            key={page.number}
                            className="bg-muted/20 border rounded p-2 text-[10px] text-muted-foreground text-center"
                          >
                            <div className="aspect-[3/4] bg-muted/30 rounded mb-1 flex items-center justify-center">
                              <FileText className="h-5 w-5 opacity-30" />
                            </div>
                            Page {page.number}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Hook Score */}
              <HookScoreDisplay score={hookScore} />
            </div>
          </TabsContent>
        </Tabs>

        {/* Guide legend */}
        {showGuides && (
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground border-t pt-3">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 border-2 border-dashed border-red-300 inline-block rounded-sm" />
              Bleed Zone
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 border border-blue-400 inline-block rounded-sm" />
              Trim Line
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 border border-green-400 inline-block rounded-sm" />
              Safe Zone
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-yellow-300/30 border border-yellow-400/50 inline-block rounded-sm" />
              Gutter Zone
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
