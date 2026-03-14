"use client";

import { useState, useMemo } from "react";
import {
  Loader2,
  MessageSquareWarning,
  Sparkles,
  Printer,
  Palette,
  Brain,
  Key,
  Type,
  BookOpen,
  ImageIcon,
  HelpCircle,
  Play,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
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
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  useAnalyzeFeedback,
  type BookType,
  type FeedbackAction,
} from "@/modules/specialty/shared/hooks/useAnalyzeFeedback";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ReviewFeedbackPanelProps {
  bookType: BookType;
  bookId: string;
}

// ---------------------------------------------------------------------------
// Category metadata
// ---------------------------------------------------------------------------

interface CategoryMeta {
  label: string;
  icon: typeof Printer;
  color: string;
  bgColor: string;
}

const CATEGORY_META: Record<string, CategoryMeta> = {
  print_quality: {
    label: "Print Quality",
    icon: Printer,
    color: "text-orange-600",
    bgColor: "bg-orange-500/10",
  },
  color_quality: {
    label: "Color Quality",
    icon: Palette,
    color: "text-violet-600",
    bgColor: "bg-violet-500/10",
  },
  difficulty: {
    label: "Difficulty",
    icon: Brain,
    color: "text-blue-600",
    bgColor: "bg-blue-500/10",
  },
  answer_keys: {
    label: "Answer Keys",
    icon: Key,
    color: "text-emerald-600",
    bgColor: "bg-emerald-500/10",
  },
  typography: {
    label: "Typography",
    icon: Type,
    color: "text-pink-600",
    bgColor: "bg-pink-500/10",
  },
  binding: {
    label: "Binding",
    icon: BookOpen,
    color: "text-amber-600",
    bgColor: "bg-amber-500/10",
  },
  content_quality: {
    label: "Content Quality",
    icon: Sparkles,
    color: "text-cyan-600",
    bgColor: "bg-cyan-500/10",
  },
  image_quality: {
    label: "Image Quality",
    icon: ImageIcon,
    color: "text-indigo-600",
    bgColor: "bg-indigo-500/10",
  },
  unknown: {
    label: "Unknown",
    icon: HelpCircle,
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
};

// ---------------------------------------------------------------------------
// Action button labels
// ---------------------------------------------------------------------------

const ACTION_LABELS: Record<string, { label: string; icon: typeof Play }> = {
  change_paper_type: { label: "Change Paper", icon: Printer },
  run_cmyk_softproof: { label: "Run CMYK Check", icon: Palette },
  adjust_ink_coverage: { label: "Adjust Ink", icon: Palette },
  adjust_difficulty_up: { label: "Increase Difficulty", icon: Brain },
  adjust_difficulty_down: { label: "Decrease Difficulty", icon: Brain },
  verify_answer_keys: { label: "Verify Answers", icon: Key },
  regenerate_answer_keys: { label: "Regenerate Keys", icon: Key },
  reformat_answer_keys: { label: "Reformat Keys", icon: Key },
  generate_large_print: { label: "Generate Large Print", icon: Type },
  improve_typography: { label: "Improve Typography", icon: Type },
  check_gutter_margins: { label: "Check Gutters", icon: BookOpen },
  recalculate_spine: { label: "Recalculate Spine", icon: BookOpen },
  run_originality_check: { label: "Originality Check", icon: Sparkles },
  increase_variety: { label: "Increase Variety", icon: Sparkles },
  check_image_dpi: { label: "Check Image DPI", icon: ImageIcon },
  manual_review: { label: "Manual Review", icon: HelpCircle },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ReviewFeedbackPanel({
  bookType,
  bookId,
}: ReviewFeedbackPanelProps) {
  const [complaintsText, setComplaintsText] = useState("");
  const analyzeFeedback = useAnalyzeFeedback();

  // ── Derived state ────────────────────────────────────────────────────────

  const actions = analyzeFeedback.data?.actions ?? [];

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of actions) {
      counts[a.category] = (counts[a.category] ?? 0) + 1;
    }
    return counts;
  }, [actions]);

  const sortedCategories = useMemo(
    () =>
      Object.entries(categoryCounts).sort(([, a], [, b]) => b - a),
    [categoryCounts],
  );

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleAnalyze = () => {
    const complaints = complaintsText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    if (complaints.length === 0) return;

    analyzeFeedback.mutate({
      complaints,
      book_type: bookType,
      book_id: bookId,
    });
  };

  const handleClear = () => {
    setComplaintsText("");
    analyzeFeedback.reset();
  };

  const handleActionClick = (action: FeedbackAction) => {
    // Placeholder: in a real implementation this would dispatch the action
    // to the appropriate backend endpoint scoped by bookType/bookId.
    console.log(
      `[ReviewFeedback] Dispatching action="${action.action}" for ${bookType}/${bookId}`,
    );
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <MessageSquareWarning className="h-5 w-5 text-primary" />
          Review Feedback Analyzer
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Paste common reader complaints from Amazon reviews (one per line) to
          get actionable fixes for your book.
        </p>
      </div>

      {/* Input area */}
      <Card>
        <CardContent className="p-4 space-y-3">
          <Textarea
            placeholder={[
              "Paste reader complaints here, one per line. For example:",
              "colors washed out",
              "pages too thin",
              "print too small",
              "answers wrong",
            ].join("\n")}
            className="min-h-[140px] font-mono text-sm"
            value={complaintsText}
            onChange={(e) => setComplaintsText(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={handleAnalyze}
              disabled={
                analyzeFeedback.isPending || complaintsText.trim().length === 0
              }
              className="gap-1.5"
            >
              {analyzeFeedback.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {analyzeFeedback.isPending
                ? "Analyzing..."
                : "Analyze Feedback"}
            </Button>
            {actions.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClear}
                className="gap-1.5 text-muted-foreground"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear Results
              </Button>
            )}
            <span className="text-xs text-muted-foreground ml-auto">
              {complaintsText
                .split("\n")
                .filter((l) => l.trim().length > 0).length}{" "}
              complaint(s)
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {actions.length > 0 && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {sortedCategories.map(([category, count]) => {
              const meta = CATEGORY_META[category] ?? CATEGORY_META.unknown;
              const Icon = meta.icon;
              return (
                <Card key={category} className="overflow-hidden">
                  <CardContent className="p-3 flex items-center gap-3">
                    <div
                      className={cn(
                        "h-9 w-9 rounded-lg flex items-center justify-center shrink-0",
                        meta.bgColor,
                      )}
                    >
                      <Icon className={cn("h-4 w-4", meta.color)} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xl font-bold leading-none">{count}</p>
                      <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                        {meta.label}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Separator />

          {/* Results table */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Analysis Results ({actions.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[180px]">Complaint</TableHead>
                    <TableHead className="w-[130px]">Category</TableHead>
                    <TableHead>Suggested Fix</TableHead>
                    <TableHead className="w-[180px] text-right">
                      Action
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {actions.map((action, idx) => {
                    const meta =
                      CATEGORY_META[action.category] ?? CATEGORY_META.unknown;
                    const CatIcon = meta.icon;
                    const actionMeta =
                      ACTION_LABELS[action.action] ?? ACTION_LABELS.manual_review;
                    const ActionIcon = actionMeta?.icon ?? Play;

                    return (
                      <TableRow key={idx}>
                        {/* Complaint */}
                        <TableCell className="font-medium text-sm align-top">
                          {action.complaint}
                        </TableCell>

                        {/* Category */}
                        <TableCell className="align-top">
                          <Badge
                            variant="secondary"
                            className={cn(
                              "gap-1 text-[11px]",
                              meta.bgColor,
                              meta.color,
                            )}
                          >
                            <CatIcon className="h-3 w-3" />
                            {meta.label}
                          </Badge>
                        </TableCell>

                        {/* Suggested Fix */}
                        <TableCell className="text-sm text-muted-foreground align-top">
                          {action.suggested_fix}
                        </TableCell>

                        {/* Action */}
                        <TableCell className="text-right align-top">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-1.5 h-7 text-xs"
                                onClick={() => handleActionClick(action)}
                              >
                                <ActionIcon className="h-3 w-3" />
                                {actionMeta?.label ?? action.action}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="max-w-[240px]">
                              <p className="text-xs">
                                Run <strong>{actionMeta?.label ?? action.action}</strong>{" "}
                                for this {bookType.replace("-books", "")} book.
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {/* Empty state after analysis with no results */}
      {analyzeFeedback.isSuccess && actions.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <HelpCircle className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="font-medium">No actionable issues found</p>
            <p className="text-sm text-muted-foreground mt-1">
              The complaints provided could not be matched to known issues.
              Try rephrasing or adding more specific feedback.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
