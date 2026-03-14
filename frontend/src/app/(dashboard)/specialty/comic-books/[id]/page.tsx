"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Users,
  FileText,
  Eye,
  Download,
  Image as ImageIcon,
  GripVertical,
  Plus,
  Wand2,
  Palette,
  MessageSquare,
  PenTool,
  Layout,
  Zap,
  Trash2,
  Square,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import {
  useComic,
  useComicPages,
  useComicCharacters,
} from "@/modules/specialty/comic/hooks";
import type { ComicPanel } from "@/modules/specialty/comic/hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  draft: "secondary",
  "in-progress": "default",
  published: "outline",
};

const PANEL_TYPES = [
  { value: "standard", label: "Standard" },
  { value: "wide", label: "Wide" },
  { value: "tall", label: "Tall" },
  { value: "splash", label: "Splash" },
  { value: "inset", label: "Inset" },
  { value: "bleed", label: "Full Bleed" },
];

const BUBBLE_TYPES = [
  { value: "speech", label: "Speech" },
  { value: "thought", label: "Thought" },
  { value: "narration", label: "Narration" },
  { value: "sfx", label: "SFX" },
  { value: "whisper", label: "Whisper" },
  { value: "shout", label: "Shout" },
];

const BORDER_STYLES = [
  { value: "solid", label: "Solid" },
  { value: "dashed", label: "Dashed" },
  { value: "rough", label: "Rough" },
  { value: "none", label: "None" },
  { value: "double", label: "Double" },
];

const LAYOUT_TEMPLATES = [
  {
    name: "2x2 Grid",
    panels: [
      { x: 2, y: 2, width: 47, height: 47 },
      { x: 51, y: 2, width: 47, height: 47 },
      { x: 2, y: 51, width: 47, height: 47 },
      { x: 51, y: 51, width: 47, height: 47 },
    ],
  },
  {
    name: "2x3 Grid",
    panels: [
      { x: 2, y: 2, width: 47, height: 30 },
      { x: 51, y: 2, width: 47, height: 30 },
      { x: 2, y: 34, width: 47, height: 30 },
      { x: 51, y: 34, width: 47, height: 30 },
      { x: 2, y: 66, width: 47, height: 30 },
      { x: 51, y: 66, width: 47, height: 30 },
    ],
  },
  {
    name: "Splash",
    panels: [{ x: 2, y: 2, width: 96, height: 96 }],
  },
  {
    name: "Hero + 2",
    panels: [
      { x: 2, y: 2, width: 96, height: 58 },
      { x: 2, y: 62, width: 47, height: 36 },
      { x: 51, y: 62, width: 47, height: 36 },
    ],
  },
  {
    name: "3 Rows",
    panels: [
      { x: 2, y: 2, width: 96, height: 30 },
      { x: 2, y: 34, width: 96, height: 30 },
      { x: 2, y: 66, width: 96, height: 30 },
    ],
  },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function ComicBookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const comicId = params.id as string;

  const { data: comic, isLoading, error } = useComic(comicId);
  const { data: pages } = useComicPages(comicId);
  const { data: characters } = useComicCharacters(comicId);

  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [selectedPanelId, setSelectedPanelId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("script");

  // Loading state
  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex-1 flex">
          <Skeleton className="w-56 h-full shrink-0" />
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-[400px] w-full" />
          </div>
          <Skeleton className="w-72 h-full shrink-0" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !comic) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push("/specialty/comic-books")}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Comic not found</h2>
          <p className="text-muted-foreground max-w-md">
            This comic could not be loaded. It may have been deleted or you may
            not have permission to view it.
          </p>
          <Button asChild variant="outline">
            <Link href="/specialty/comic-books">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Return to Comics
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const currentPage = pages?.[selectedPageIndex];
  const currentPanels: ComicPanel[] = currentPage?.panels ?? [];
  const selectedPanel = currentPanels.find((p) => p.id === selectedPanelId);

  // Script stats
  const totalPanels =
    pages?.reduce((sum, p) => sum + (p.panels?.length ?? 0), 0) ?? 0;
  const totalWords =
    pages?.reduce((sum, p) => {
      const scriptWords =
        p.script_text?.split(/\s+/).filter(Boolean).length ?? 0;
      const bubbleWords =
        p.panels?.reduce(
          (ps, panel) =>
            ps +
            (panel.bubbles?.reduce(
              (bs, b) =>
                bs + (b.text?.split(/\s+/).filter(Boolean).length ?? 0),
              0,
            ) ?? 0),
          0,
        ) ?? 0;
      return sum + scriptWords + bubbleWords;
    }, 0) ?? 0;

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb */}
      <div className="px-4 pt-2">
        <Breadcrumb items={[
          { label: "Specialty", href: "/specialty" },
          { label: "Comic Books", href: "/specialty/comic-books" },
          { label: comic.title },
        ]} />
      </div>
      {/* Header */}
      <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => router.push("/specialty/comic-books")}
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-base font-semibold truncate">{comic.title}</h1>
          <Badge
            variant={STATUS_VARIANT[comic.status] ?? "secondary"}
            className="shrink-0 capitalize"
          >
            {comic.status}
          </Badge>
          {comic.genre && (
            <Badge variant="outline" className="shrink-0">
              {comic.genre}
            </Badge>
          )}
        </div>
        <div className="flex-1" />
        <span className="text-sm text-muted-foreground">
          {comic.page_count} pages
        </span>
        <Button size="sm" variant="outline" className="gap-1.5">
          <Download className="h-3.5 w-3.5" />
          Export
        </Button>
        <Button size="sm" variant="outline" className="gap-1.5">
          <Eye className="h-3.5 w-3.5" />
          Preflight
        </Button>
      </div>

      {/* Tab Navigation */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex-1 flex flex-col overflow-hidden"
      >
        <div className="border-b px-4">
          <TabsList className="h-10">
            <TabsTrigger value="script" className="gap-1.5">
              <PenTool className="h-3.5 w-3.5" />
              Script
            </TabsTrigger>
            <TabsTrigger value="visual" className="gap-1.5">
              <Layout className="h-3.5 w-3.5" />
              Visual
            </TabsTrigger>
          </TabsList>
        </div>

        {/* ================================================================= */}
        {/* SCRIPT EDITOR TAB                                                 */}
        {/* ================================================================= */}
        <TabsContent value="script" className="flex-1 overflow-hidden m-0">
          <div className="flex h-full">
            {/* Left: Page List */}
            <div className="w-56 border-r bg-muted/30 shrink-0 flex flex-col">
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-xs font-semibold text-muted-foreground uppercase">
                  Pages
                </span>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Plus className="h-3.5 w-3.5" />
                </Button>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                  {pages?.map((page, idx) => (
                    <button
                      key={page.id}
                      onClick={() => {
                        setSelectedPageIndex(idx);
                        setSelectedPanelId(null);
                      }}
                      className={cn(
                        "w-full flex items-center gap-2 rounded-md p-2 text-left transition-colors",
                        idx === selectedPageIndex
                          ? "bg-primary/10 ring-1 ring-primary"
                          : "hover:bg-muted",
                      )}
                    >
                      <GripVertical className="h-3 w-3 text-muted-foreground shrink-0 cursor-grab" />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium">
                          Page {page.page_number}
                        </span>
                        <p className="text-[10px] text-muted-foreground truncate">
                          {page.panels?.length ?? 0} panels
                        </p>
                      </div>
                    </button>
                  )) ?? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      No pages yet
                    </p>
                  )}
                </div>
              </ScrollArea>
              <div className="p-2 border-t">
                <Button variant="outline" size="sm" className="w-full gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  Add Page
                </Button>
              </div>
            </div>

            {/* Center: Script Panel */}
            <div className="flex-1 overflow-auto">
              <ScrollArea className="h-full">
                <div className="p-6 max-w-3xl mx-auto space-y-6">
                  {currentPage ? (
                    <>
                      <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold">
                          Page {currentPage.page_number} Script
                        </h2>
                        <Badge variant="outline">
                          {currentPanels.length} panels
                        </Badge>
                      </div>

                      {currentPanels.length > 0 ? (
                        <div className="space-y-4">
                          {currentPanels.map((panel) => (
                            <Card
                              key={panel.id}
                              className={cn(
                                "transition-all cursor-pointer",
                                selectedPanelId === panel.id &&
                                  "ring-2 ring-primary",
                              )}
                              onClick={() => setSelectedPanelId(panel.id)}
                            >
                              <CardHeader className="pb-2">
                                <div className="flex items-center gap-2">
                                  <Badge
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    Panel {panel.panel_number}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground capitalize">
                                    {panel.panel_type}
                                  </span>
                                </div>
                              </CardHeader>
                              <CardContent className="space-y-3">
                                <div className="space-y-1">
                                  <Label className="text-xs text-muted-foreground">
                                    Description
                                  </Label>
                                  <Textarea
                                    className="text-sm min-h-[60px]"
                                    placeholder="Describe the scene in this panel..."
                                    defaultValue={panel.description ?? ""}
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label className="text-xs text-muted-foreground flex items-center gap-1">
                                    <MessageSquare className="h-3 w-3" />
                                    Dialogue
                                  </Label>
                                  {(panel.bubbles?.length ?? 0) > 0 ? (
                                    <div className="space-y-2">
                                      {panel.bubbles!.map((bubble) => (
                                        <div
                                          key={bubble.id}
                                          className="flex gap-2 items-start bg-muted/50 rounded-md p-2"
                                        >
                                          <Badge
                                            variant="outline"
                                            className="text-[10px] shrink-0 mt-0.5"
                                          >
                                            {bubble.character_name ||
                                              bubble.type}
                                          </Badge>
                                          <Input
                                            className="text-sm h-auto"
                                            defaultValue={bubble.text}
                                            placeholder="Dialogue text..."
                                          />
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <p className="text-xs text-muted-foreground italic">
                                      No dialogue yet
                                    </p>
                                  )}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs gap-1"
                                  >
                                    <Plus className="h-3 w-3" />
                                    Add Dialogue
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Label className="text-xs text-muted-foreground">
                            Full Page Script
                          </Label>
                          <Textarea
                            className="min-h-[300px] text-sm"
                            placeholder="Write the script for this page..."
                            defaultValue={currentPage.script_text ?? ""}
                          />
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center text-muted-foreground py-16">
                      <BookOpen className="h-16 w-16 mx-auto mb-3" />
                      <p className="text-lg font-medium">No pages yet</p>
                      <p className="text-sm">
                        Add pages to start writing your comic script.
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>

            {/* Right: Script Tools */}
            <div className="w-64 border-l shrink-0 flex flex-col">
              <ScrollArea className="flex-1">
                <div className="p-4 space-y-5">
                  {/* AI Script Tools */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase">
                      AI Script Tools
                    </h3>
                    <div className="space-y-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start gap-2 h-8"
                      >
                        <Wand2 className="h-3.5 w-3.5" />
                        Generate Full Script
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start gap-2 h-8"
                        disabled={!selectedPanelId}
                      >
                        <Zap className="h-3.5 w-3.5" />
                        Expand Panel
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start gap-2 h-8"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        Generate Next Page
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  {/* Characters */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      Characters
                    </h3>
                    {characters && characters.length > 0 ? (
                      <div className="space-y-1">
                        {characters.map((char) => (
                          <button
                            key={char.id}
                            className="w-full text-left rounded-md p-2 hover:bg-muted transition-colors"
                            title="Click to insert character name"
                          >
                            <p className="text-sm font-medium">{char.name}</p>
                            <p className="text-[10px] text-muted-foreground capitalize">
                              {char.role}
                            </p>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground italic">
                        No characters defined
                      </p>
                    )}
                  </div>

                  <Separator />

                  {/* Script Stats */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase">
                      Script Stats
                    </h3>
                    <Card>
                      <CardContent className="p-3 space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Pages</span>
                          <span className="font-medium">
                            {pages?.length ?? 0}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Panels</span>
                          <span className="font-medium">{totalPanels}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Words</span>
                          <span className="font-medium">{totalWords}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">
                            Est. Read Time
                          </span>
                          <span className="font-medium">
                            {Math.max(1, Math.round(totalWords / 200))} min
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </ScrollArea>
            </div>
          </div>
        </TabsContent>

        {/* ================================================================= */}
        {/* VISUAL EDITOR TAB                                                 */}
        {/* ================================================================= */}
        <TabsContent value="visual" className="flex-1 overflow-hidden m-0">
          <div className="flex h-full">
            {/* Left: Page Thumbnails + Templates */}
            <div className="w-56 border-r bg-muted/30 shrink-0 flex flex-col">
              <div className="px-3 py-2">
                <span className="text-xs font-semibold text-muted-foreground uppercase">
                  Pages
                </span>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-2 space-y-2">
                  {pages?.map((page, idx) => (
                    <button
                      key={page.id}
                      onClick={() => {
                        setSelectedPageIndex(idx);
                        setSelectedPanelId(null);
                      }}
                      className={cn(
                        "w-full rounded-md transition-colors",
                        idx === selectedPageIndex
                          ? "ring-2 ring-primary"
                          : "hover:ring-1 hover:ring-muted-foreground/30",
                      )}
                    >
                      <div className="aspect-[3/4] bg-white rounded-md border relative overflow-hidden">
                        {page.panels?.map((panel) => (
                          <div
                            key={panel.id}
                            className="absolute border border-muted-foreground/20 bg-muted/30 rounded-[2px]"
                            style={{
                              left: `${panel.x}%`,
                              top: `${panel.y}%`,
                              width: `${panel.width}%`,
                              height: `${panel.height}%`,
                            }}
                          />
                        ))}
                        <div className="absolute bottom-0 inset-x-0 bg-black/50 px-1.5 py-0.5">
                          <span className="text-[9px] text-white font-medium">
                            Page {page.page_number}
                          </span>
                        </div>
                      </div>
                    </button>
                  )) ?? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      No pages yet
                    </p>
                  )}

                  <Separator className="my-3" />
                  <span className="text-xs font-semibold text-muted-foreground uppercase px-1">
                    Layout Templates
                  </span>
                  <div className="grid grid-cols-3 gap-1.5 mt-2">
                    {LAYOUT_TEMPLATES.map((tmpl) => (
                      <button
                        key={tmpl.name}
                        className="aspect-[3/4] bg-white rounded border hover:ring-1 hover:ring-primary relative overflow-hidden group"
                        title={tmpl.name}
                      >
                        {tmpl.panels.map((p, i) => (
                          <div
                            key={i}
                            className="absolute border border-muted-foreground/30 bg-muted/20 group-hover:bg-primary/10 transition-colors"
                            style={{
                              left: `${p.x}%`,
                              top: `${p.y}%`,
                              width: `${p.width}%`,
                              height: `${p.height}%`,
                            }}
                          />
                        ))}
                      </button>
                    ))}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2 text-xs"
                    disabled={!currentPage}
                  >
                    Apply Template
                  </Button>
                </div>
              </ScrollArea>
            </div>

            {/* Center: Canvas */}
            <div className="flex-1 flex items-center justify-center p-6 overflow-auto bg-muted/10">
              {currentPage ? (
                <div className="w-full max-w-2xl">
                  <div className="aspect-[3/4] bg-white rounded-lg shadow-md border relative overflow-hidden">
                    {currentPanels.length > 0 ? (
                      currentPanels.map((panel) => (
                        <button
                          key={panel.id}
                          onClick={() => setSelectedPanelId(panel.id)}
                          className={cn(
                            "absolute border-2 rounded transition-all flex flex-col items-center justify-center gap-1 group",
                            selectedPanelId === panel.id
                              ? "border-primary bg-primary/5 shadow-lg"
                              : "border-muted-foreground/30 hover:border-primary/50 bg-muted/10",
                          )}
                          style={{
                            left: `${panel.x}%`,
                            top: `${panel.y}%`,
                            width: `${panel.width}%`,
                            height: `${panel.height}%`,
                          }}
                        >
                          {panel.art_url ? (
                            <img
                              src={panel.art_url}
                              alt={`Panel ${panel.panel_number}`}
                              className="h-full w-full object-cover rounded"
                            />
                          ) : (
                            <>
                              <Badge
                                variant={
                                  selectedPanelId === panel.id
                                    ? "default"
                                    : "secondary"
                                }
                                className="text-[10px]"
                              >
                                {panel.panel_number}
                              </Badge>
                              <span className="text-[9px] text-muted-foreground group-hover:text-foreground transition-colors">
                                {panel.panel_type}
                              </span>
                            </>
                          )}
                          {(panel.bubbles?.length ?? 0) > 0 && (
                            <div className="absolute top-1 right-1 flex gap-0.5">
                              {panel.bubbles!.map((b) => (
                                <div
                                  key={b.id}
                                  className={cn(
                                    "h-2 w-2 rounded-full",
                                    b.type === "speech" && "bg-blue-400",
                                    b.type === "thought" && "bg-purple-400",
                                    b.type === "narration" && "bg-amber-400",
                                    b.type === "sfx" && "bg-red-400",
                                    b.type === "whisper" && "bg-gray-400",
                                    b.type === "shout" && "bg-orange-400",
                                  )}
                                  title={`${b.type}: ${b.text}`}
                                />
                              ))}
                            </div>
                          )}
                        </button>
                      ))
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3">
                        <Square className="h-12 w-12" />
                        <p className="text-sm font-medium">No panels</p>
                        <p className="text-xs">
                          Select a template or add panels manually
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-center gap-2 mt-3">
                    <Button variant="outline" size="sm" className="gap-1.5">
                      <Plus className="h-3.5 w-3.5" />
                      Add Panel
                    </Button>
                    {selectedPanelId && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete Panel
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted-foreground">
                  <BookOpen className="h-16 w-16 mx-auto mb-3" />
                  <p className="text-lg font-medium">No pages yet</p>
                  <p className="text-sm">
                    Add pages to start designing your comic layout.
                  </p>
                </div>
              )}
            </div>

            {/* Right: Panel Properties */}
            <div className="w-72 border-l shrink-0 flex flex-col">
              <ScrollArea className="flex-1">
                <div className="p-4 space-y-4">
                  <h3 className="font-semibold text-sm">Panel Properties</h3>
                  <Separator />

                  {selectedPanel ? (
                    <>
                      <div className="space-y-2">
                        <Label className="text-xs">Panel Type</Label>
                        <Select defaultValue={selectedPanel.panel_type}>
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {PANEL_TYPES.map((t) => (
                              <SelectItem key={t.value} value={t.value}>
                                {t.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs">Position</Label>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-[10px]">X (%)</Label>
                            <Input
                              type="number"
                              className="h-7 text-xs"
                              defaultValue={selectedPanel.x}
                              min={0}
                              max={100}
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px]">Y (%)</Label>
                            <Input
                              type="number"
                              className="h-7 text-xs"
                              defaultValue={selectedPanel.y}
                              min={0}
                              max={100}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs">Size</Label>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-[10px]">Width (%)</Label>
                            <Input
                              type="number"
                              className="h-7 text-xs"
                              defaultValue={selectedPanel.width}
                              min={1}
                              max={100}
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px]">Height (%)</Label>
                            <Input
                              type="number"
                              className="h-7 text-xs"
                              defaultValue={selectedPanel.height}
                              min={1}
                              max={100}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs">Border Style</Label>
                        <Select
                          defaultValue={selectedPanel.border_style || "solid"}
                        >
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {BORDER_STYLES.map((s) => (
                              <SelectItem key={s.value} value={s.value}>
                                {s.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs flex items-center gap-1">
                          <Palette className="h-3 w-3" />
                          Background Color
                        </Label>
                        <Input
                          type="color"
                          className="h-8 w-full cursor-pointer"
                          defaultValue={
                            selectedPanel.background_color || "#ffffff"
                          }
                        />
                      </div>

                      <Separator />

                      <div className="space-y-2">
                        <Label className="text-xs flex items-center gap-1">
                          <ImageIcon className="h-3 w-3" />
                          Art Prompt
                        </Label>
                        <Textarea
                          className="text-xs min-h-[80px]"
                          placeholder="Describe the art for this panel..."
                          defaultValue={selectedPanel.art_prompt ?? ""}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full gap-1.5"
                        >
                          <Wand2 className="h-3.5 w-3.5" />
                          Generate Art
                        </Button>
                      </div>

                      {selectedPanel.art_url && (
                        <div className="space-y-1">
                          <Label className="text-xs">Art Preview</Label>
                          <div className="aspect-video bg-muted rounded border overflow-hidden">
                            <img
                              src={selectedPanel.art_url}
                              alt={`Panel ${selectedPanel.panel_number} art`}
                              className="h-full w-full object-contain"
                            />
                          </div>
                        </div>
                      )}

                      {selectedPanel.art_model && (
                        <div className="text-[10px] text-muted-foreground bg-muted/50 rounded p-2">
                          <span className="font-medium">Model:</span>{" "}
                          {selectedPanel.art_model}
                        </div>
                      )}

                      <Separator />

                      <div className="space-y-2">
                        <Label className="text-xs flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          Bubbles
                        </Label>
                        {(selectedPanel.bubbles?.length ?? 0) > 0 ? (
                          <div className="space-y-3">
                            {selectedPanel.bubbles!.map((bubble) => (
                              <Card key={bubble.id} className="p-2 space-y-2">
                                <div className="flex items-center gap-1.5">
                                  <Select defaultValue={bubble.type}>
                                    <SelectTrigger className="h-6 text-[10px] flex-1">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {BUBBLE_TYPES.map((bt) => (
                                        <SelectItem
                                          key={bt.value}
                                          value={bt.value}
                                        >
                                          {bt.label}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 text-destructive hover:text-destructive"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                                <Input
                                  className="h-7 text-xs"
                                  placeholder="Character name"
                                  defaultValue={bubble.character_name ?? ""}
                                />
                                <Textarea
                                  className="text-xs min-h-[40px]"
                                  placeholder="Dialogue text..."
                                  defaultValue={bubble.text}
                                />
                                <div className="grid grid-cols-2 gap-1">
                                  <div className="space-y-0.5">
                                    <Label className="text-[9px]">X</Label>
                                    <Input
                                      type="number"
                                      className="h-6 text-[10px]"
                                      defaultValue={bubble.x}
                                    />
                                  </div>
                                  <div className="space-y-0.5">
                                    <Label className="text-[9px]">Y</Label>
                                    <Input
                                      type="number"
                                      className="h-6 text-[10px]"
                                      defaultValue={bubble.y}
                                    />
                                  </div>
                                </div>
                              </Card>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-muted-foreground italic">
                            No bubbles on this panel
                          </p>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full gap-1.5"
                        >
                          <Plus className="h-3.5 w-3.5" />
                          Add Bubble
                        </Button>
                      </div>
                    </>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      {currentPanels.length > 0
                        ? "Select a panel to edit its properties."
                        : "No panels on this page. Add panels or apply a template."}
                    </p>
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
