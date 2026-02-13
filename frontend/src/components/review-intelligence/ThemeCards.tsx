"use client";

import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useTranslations } from "@/hooks/use-translations";

interface ThemeItem {
  theme: string;
  count: number;
}

interface ThemeCardsProps {
  positiveThemes: ThemeItem[];
  negativeThemes: ThemeItem[];
}

function ThemeList({
  themes,
  accent,
  emptyLabel,
}: {
  themes: ThemeItem[];
  accent: "green" | "red";
  emptyLabel: string;
}) {
  const limited = themes.slice(0, 5);

  if (limited.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">{emptyLabel}</p>
    );
  }

  return (
    <ol className="space-y-2">
      {limited.map((item, idx) => (
        <li key={item.theme} className="flex items-center justify-between text-sm">
          <span>
            <span className="text-muted-foreground mr-2">{idx + 1}.</span>
            {item.theme}
          </span>
          <span
            className={
              accent === "green"
                ? "text-xs font-medium text-green-700 bg-green-100 dark:text-green-400 dark:bg-green-900/30 px-2 py-0.5 rounded-full"
                : "text-xs font-medium text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/30 px-2 py-0.5 rounded-full"
            }
          >
            {item.count}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function ThemeCards({ positiveThemes, negativeThemes }: ThemeCardsProps) {
  const t = useTranslations("reviews");

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Positive Themes */}
      <Card className="border-l-4 border-l-green-500">
        <CardHeader className="pb-3">
          <h4 className="text-sm font-semibold text-green-700 dark:text-green-400">
            {t("insights.positiveThemes")}
          </h4>
        </CardHeader>
        <CardContent>
          <ThemeList
            themes={positiveThemes}
            accent="green"
            emptyLabel={t("insights.noThemes")}
          />
        </CardContent>
      </Card>

      {/* Negative Themes */}
      <Card className="border-l-4 border-l-red-500">
        <CardHeader className="pb-3">
          <h4 className="text-sm font-semibold text-red-700 dark:text-red-400">
            {t("insights.negativeThemes")}
          </h4>
        </CardHeader>
        <CardContent>
          <ThemeList
            themes={negativeThemes}
            accent="red"
            emptyLabel={t("insights.noThemes")}
          />
        </CardContent>
      </Card>
    </div>
  );
}
