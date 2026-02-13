"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/hooks/use-translations";
import { useGenerateEmailSequence } from "@/modules/reviews/hooks";
import type { EmailSequenceEmail } from "@/modules/reviews/hooks";

interface EmailSequenceBuilderProps {
  bookId?: string;
}

interface DefaultTemplate {
  nameKey: string;
  day: number;
}

const DEFAULT_TEMPLATES: DefaultTemplate[] = [
  { nameKey: "acquisition.emailTemplates.thankYou", day: 1 },
  { nameKey: "acquisition.emailTemplates.howsItGoing", day: 7 },
  { nameKey: "acquisition.emailTemplates.reviewRequest", day: 14 },
  { nameKey: "acquisition.emailTemplates.gentleReminder", day: 21 },
];

export function EmailSequenceBuilder({ bookId }: EmailSequenceBuilderProps) {
  const t = useTranslations("reviews");
  const generateSequence = useGenerateEmailSequence();
  const [generatedEmails, setGeneratedEmails] = useState<EmailSequenceEmail[] | null>(null);

  const handleGenerate = () => {
    if (!bookId) return;
    generateSequence.mutate(
      { book_id: bookId, timing: DEFAULT_TEMPLATES.map((tpl) => tpl.day) },
      {
        onSuccess: (data) => {
          setGeneratedEmails(data.emails);
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base">
              {t("acquisition.emailSequenceTitle")}
            </CardTitle>
            <CardDescription>
              {t("acquisition.emailSequenceSubtitle")}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleGenerate}
              disabled={!bookId || generateSequence.isPending}
            >
              {generateSequence.isPending
                ? t("acquisition.generating")
                : t("acquisition.generateNewSequence")}
            </Button>
            <Button variant="outline" size="sm" disabled>
              {t("acquisition.customizeTiming")}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Default template list */}
        <div className="space-y-2">
          {DEFAULT_TEMPLATES.map((template, index) => (
            <div
              key={template.day}
              className="flex items-center justify-between rounded-lg border p-3"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium">{t(template.nameKey)}</p>
                  <p className="text-xs text-muted-foreground">
                    {t("acquisition.dayLabel", { day: template.day })}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm">
                  {t("acquisition.preview")}
                </Button>
                <Button variant="outline" size="sm">
                  {t("acquisition.edit")}
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Generated emails */}
        {generatedEmails && generatedEmails.length > 0 && (
          <div className="mt-6">
            <h4 className="mb-3 text-sm font-semibold">
              {t("acquisition.generatedEmails")}
            </h4>
            <div className="space-y-3">
              {generatedEmails.map((email, index) => (
                <div
                  key={index}
                  className="rounded-lg border bg-muted/40 p-4"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      {t("acquisition.dayLabel", { day: email.send_day })}
                    </span>
                  </div>
                  <p className="mt-1 text-sm font-medium">{email.subject}</p>
                  <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">
                    {email.body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
