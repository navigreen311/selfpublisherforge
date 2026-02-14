"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Loader2,
  Search,
  X,
  Plus,
  Copy,
  Check,
  ArrowUpDown,
  Star,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { useOptimizeKeywordsMutation } from "../hooks";
import type { KeywordRecommendation } from "../types";

interface KeywordOptimizerTabProps {
  className?: string;
}

type SortField = "keyword" | "search_vol" | "competition" | "relevance";
type SortDir = "asc" | "desc";

const COMPETITION_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-red-100 text-red-800",
};

function RelevanceStars({ value }: { value: number }) {
  const stars = Math.min(Math.max(Math.round(value * 5), 0), 5);
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            "h-3.5 w-3.5",
            i < stars
              ? "fill-yellow-400 text-yellow-400"
              : "fill-none text-gray-300"
          )}
        />
      ))}
    </div>
  );
}

export function KeywordOptimizerTab({ className }: KeywordOptimizerTabProps) {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [genre, setGenre] = useState("");
  const [title, setTitle] = useState("");
  const [sortField, setSortField] = useState<SortField>("relevance");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [copied, setCopied] = useState(false);

  const optimizeMutation = useOptimizeKeywordsMutation();

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords([...keywords, kw]);
      setKeywordInput("");
    }
  };

  const removeKeyword = (kw: string) => {
    setKeywords(keywords.filter((k) => k !== kw));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addKeyword();
    }
  };

  const handleAnalyze = () => {
    if (!title.trim()) return;

    optimizeMutation.mutate({
      current_keywords: keywords,
      genre: genre.trim() || "general",
      title: title.trim(),
    });
  };

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const sortedRecommendations = (optimizeMutation.data?.recommended ?? [])
    .slice()
    .sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      switch (sortField) {
        case "keyword":
          return dir * a.keyword.localeCompare(b.keyword);
        case "search_vol":
          return dir * (a.search_vol - b.search_vol);
        case "competition": {
          const compOrder = { low: 1, medium: 2, high: 3 };
          return dir * (compOrder[a.competition] - compOrder[b.competition]);
        }
        case "relevance":
          return dir * (a.relevance - b.relevance);
        default:
          return 0;
      }
    });

  const handleCopyOptimal = async () => {
    const optimal = optimizeMutation.data?.optimal_seven ?? [];
    try {
      await navigator.clipboard.writeText(optimal.join(", "));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Input section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-5 w-5" />
            Keyword Optimizer
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="kw-title">Book Title</Label>
              <Input
                id="kw-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Your book title"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="kw-genre">Genre</Label>
              <Input
                id="kw-genre"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                placeholder="e.g., Romance, Thriller, Self-Help"
              />
            </div>
          </div>

          {/* Keyword tags */}
          <div className="space-y-2">
            <Label>Current Keywords</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {keywords.map((kw) => (
                <Badge
                  key={kw}
                  variant="secondary"
                  className="flex items-center gap-1 pr-1"
                >
                  {kw}
                  <button
                    onClick={() => removeKeyword(kw)}
                    className="ml-1 rounded-full p-0.5 hover:bg-muted"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a keyword and press Enter"
              />
              <Button variant="outline" size="sm" onClick={addKeyword} disabled={!keywordInput.trim()}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Button onClick={handleAnalyze} disabled={!title.trim() || optimizeMutation.isPending}>
            {optimizeMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze &amp; Recommend
              </>
            )}
          </Button>

          {optimizeMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to optimize keywords. Please try again.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {optimizeMutation.data && (
        <div className="space-y-6">
          {/* Recommendations table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Recommended Keywords</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => toggleSort("keyword")}
                      >
                        Keyword
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => toggleSort("search_vol")}
                      >
                        Search Vol
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => toggleSort("competition")}
                      >
                        Competition
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => toggleSort("relevance")}
                      >
                        Relevance
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedRecommendations.map((rec: KeywordRecommendation) => (
                    <TableRow key={rec.keyword}>
                      <TableCell className="font-medium">{rec.keyword}</TableCell>
                      <TableCell>{rec.search_vol.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn("text-xs capitalize", COMPETITION_COLORS[rec.competition])}
                        >
                          {rec.competition}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <RelevanceStars value={rec.relevance} />
                      </TableCell>
                    </TableRow>
                  ))}
                  {sortedRecommendations.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                        No keyword recommendations available.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Optimal 7 */}
          {optimizeMutation.data.optimal_seven.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Optimal 7 Keywords</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md bg-muted p-4">
                  <p className="text-sm font-medium">
                    {optimizeMutation.data.optimal_seven.join(", ")}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={handleCopyOptimal}
                >
                  {copied ? (
                    <>
                      <Check className="mr-1.5 h-3 w-3" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1.5 h-3 w-3" />
                      Copy Keywords
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
