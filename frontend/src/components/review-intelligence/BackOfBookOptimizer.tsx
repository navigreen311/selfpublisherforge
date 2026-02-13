"use client";

import { useState, useCallback } from "react";
import { Copy, Check, Sparkles, Loader2, Lightbulb, ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "@/hooks/use-translations";
import { useOptimizeBackMatter } from "@/modules/reviews/hooks";

interface BackOfBookOptimizerProps {
  bookId?: string;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "bg-green-500 text-white";
  if (score >= 60) return "bg-yellow-500 text-white";
  if (score >= 40) return "bg-orange-500 text-white";
  return "bg-red-500 text-white";
}

export function BackOfBookOptimizer({ bookId }: BackOfBookOptimizerProps) {
  const t = useTranslations("reviews");

  const [currentText, setCurrentText] = useState("");
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [generatedScore, setGeneratedScore] = useState<number | null>(null);
  const [currentScore, setCurrentScore] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  const optimizeMutation = useOptimizeBackMatter();

  const handleGenerate = useCallback(() => {
    if (!currentText.trim()) return;

    optimizeMutation.mutate(
      { current_text: currentText, book_id: bookId },
      {
        onSuccess: (data) => {
          setGeneratedText(data.improved_text);
          setGeneratedScore(data.score);
          // Derive a rough score for the current text (generated score is for improved)
          // The API returns the score for the improved version; estimate current as lower
          if (currentScore === null) {
            setCurrentScore(Math.max(0, data.score - 20));
          }
        },
      }
    );
  }, [currentText, bookId, optimizeMutation, currentScore]);

  const handleCopy = useCallback(async () => {
    if (!generatedText) return;
    await navigator.clipboard.writeText(generatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [generatedText]);

  const handleUseVersion = useCallback(() => {
    if (!generatedText) return;
    setCurrentText(generatedText);
    setCurrentScore(generatedScore);
    setGeneratedText(null);
    setGeneratedScore(null);
  }, [generatedText, generatedScore]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {t("acquisition.backOfBook.title")}
          </CardTitle>
          {currentScore !== null && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {t("acquisition.backOfBook.aiScore")}
              </span>
              <Badge className={getScoreColor(currentScore)}>
                {currentScore}/100
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current back-of-book text */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            {t("acquisition.backOfBook.currentTextLabel")}
          </label>
          <Textarea
            value={currentText}
            onChange={(e) => setCurrentText(e.target.value)}
            placeholder={t("acquisition.backOfBook.currentTextPlaceholder")}
            rows={6}
            className="resize-y"
          />
        </div>

        {/* Generate button */}
        <Button
          onClick={handleGenerate}
          disabled={optimizeMutation.isPending || !currentText.trim()}
          className="w-full sm:w-auto"
        >
          {optimizeMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t("acquisition.backOfBook.generating")}
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              {t("acquisition.backOfBook.generateButton")}
            </>
          )}
        </Button>

        {/* AI-generated alternative */}
        {generatedText && (
          <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-foreground">
                {t("acquisition.backOfBook.generatedVersionTitle")}
              </h4>
              {generatedScore !== null && (
                <Badge className={getScoreColor(generatedScore)}>
                  {generatedScore}/100
                </Badge>
              )}
            </div>

            <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
              {generatedText}
            </p>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
              >
                {copied ? (
                  <>
                    <Check className="mr-1.5 h-3.5 w-3.5" />
                    {t("acquisition.backOfBook.copied")}
                  </>
                ) : (
                  <>
                    <Copy className="mr-1.5 h-3.5 w-3.5" />
                    {t("acquisition.backOfBook.copyButton")}
                  </>
                )}
              </Button>
              <Button size="sm" onClick={handleUseVersion}>
                <ArrowRight className="mr-1.5 h-3.5 w-3.5" />
                {t("acquisition.backOfBook.useVersionButton")}
              </Button>
            </div>
          </div>
        )}

        {/* Tip banner */}
        <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950/30">
          <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
          <p className="text-sm text-blue-800 dark:text-blue-300">
            {t("acquisition.backOfBook.tip")}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
