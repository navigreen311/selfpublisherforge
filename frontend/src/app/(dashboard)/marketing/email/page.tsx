"use client";

import { useSearchParams } from "next/navigation";
import { useEmailSequences, useCreateEmailSequence, useTriggerEmailSend } from "@/modules/marketing/hooks";
import { EmailSequenceBuilder } from "@/modules/marketing/components/EmailSequenceBuilder";
import { toast } from "sonner";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function EmailSequencePage() {
  const t = useTranslations("marketing");
  const searchParams = useSearchParams();
  const sequenceId = searchParams.get("id");

  const { data: sequencesData, isLoading } = useEmailSequences();
  const createMutation = useCreateEmailSequence();

  const selectedSequence = sequenceId
    ? sequencesData?.items?.find((s) => s.id === sequenceId)
    : undefined;

  const validateEmailSequence = (data: {
    name: string;
    description?: string;
    emails: Array<Record<string, unknown>>;
  }): string[] => {
    const errors: string[] = [];
    const trimmedName = data.name.trim();
    if (!trimmedName) {
      errors.push(t("email.validationError.nameRequired"));
    } else if (trimmedName.length < 2) {
      errors.push(t("email.validationError.nameMin"));
    } else if (trimmedName.length > 100) {
      errors.push(t("email.validationError.nameMax"));
    }

    if (!data.emails || data.emails.length === 0) {
      errors.push(t("email.validationError.emailsRequired"));
    } else {
      data.emails.forEach((email, index) => {
        const emailNum = index + 1;
        const subject = (email.subject as string) || "";
        const body = (email.body_html as string) || "";

        if (!subject.trim()) {
          errors.push(t("email.validationError.subjectRequired", { num: emailNum }));
        } else if (subject.trim().length > 200) {
          errors.push(t("email.validationError.subjectMax", { num: emailNum }));
        }

        if (!body.trim()) {
          errors.push(t("email.validationError.bodyRequired", { num: emailNum }));
        } else if (body.trim().length < 10) {
          errors.push(t("email.validationError.bodyMin", { num: emailNum }));
        }
      });
    }

    return errors;
  };

  const handleSave = (data: {
    name: string;
    description?: string;
    emails: Array<Record<string, unknown>>;
  }) => {
    const validationErrors = validateEmailSequence(data);
    if (validationErrors.length > 0) {
      validationErrors.forEach((err) => toast.error(err));
      return;
    }

    createMutation.mutate(
      {
        name: data.name,
        description: data.description,
        emails: data.emails as never[],
      } as never,
      {
        onSuccess: () => {
          toast.success(t("email.saveSuccess"));
        },
        onError: () => {
          toast.error(t("email.saveError"));
        },
      }
    );
  };

  const handleSend = (recipientEmails: string[]) => {
    toast.info(t("email.sendingTo", { count: recipientEmails.length }));
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link href="/marketing" className="hover:text-blue-600">
          {t("title")}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-700">{t("email.breadcrumb")}</span>
      </nav>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Sequence List */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="font-semibold text-sm text-gray-500 uppercase tracking-wider">
            {t("email.sequencesLabel")}
          </h3>
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : (
            <>
              {sequencesData?.items?.map((seq) => (
                <Link
                  key={seq.id}
                  href={`/marketing/email?id=${seq.id}`}
                  className={`block p-3 rounded-lg border text-sm transition-colors ${
                    seq.id === sequenceId
                      ? "bg-blue-50 border-blue-300"
                      : "bg-white hover:bg-gray-50"
                  }`}
                >
                  <div className="font-medium truncate">{seq.name}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {t("email.sequenceStatus", { status: seq.status, sent: seq.sent_count, total: seq.recipient_count })}
                  </div>
                </Link>
              ))}
              {(!sequencesData?.items || sequencesData.items.length === 0) && (
                <div className="p-3 text-center">
                  <p className="text-sm text-muted-foreground">{t("email.noSequences")}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t("email.noSequencesHint")}</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Main Builder */}
        <div className="lg:col-span-3 bg-white rounded-lg border p-6">
          <EmailSequenceBuilder
            sequence={selectedSequence as never}
            onSave={handleSave}
            onSend={handleSend}
          />
        </div>
      </div>
    </div>
  );
}
