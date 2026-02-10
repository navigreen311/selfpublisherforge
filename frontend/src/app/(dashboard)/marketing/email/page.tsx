"use client";

import { useSearchParams } from "next/navigation";
import { useEmailSequences, useCreateEmailSequence, useTriggerEmailSend } from "@/modules/marketing/hooks";
import { EmailSequenceBuilder } from "@/modules/marketing/components/EmailSequenceBuilder";
import { toast } from "sonner";
import Link from "next/link";

export default function EmailSequencePage() {
  const searchParams = useSearchParams();
  const sequenceId = searchParams.get("id");

  const { data: sequencesData, isLoading } = useEmailSequences();
  const createMutation = useCreateEmailSequence();

  const selectedSequence = sequenceId
    ? sequencesData?.items?.find((s) => s.id === sequenceId)
    : undefined;

  const handleSave = (data: {
    name: string;
    description?: string;
    emails: Array<Record<string, unknown>>;
  }) => {
    createMutation.mutate(
      {
        name: data.name,
        description: data.description,
        emails: data.emails as never[],
      } as never,
      {
        onSuccess: () => {
          toast.success("Email sequence saved successfully");
        },
        onError: () => {
          toast.error("Failed to save email sequence");
        },
      }
    );
  };

  const handleSend = (recipientEmails: string[]) => {
    // In production, this would use the trigger send endpoint
    toast.info(`Sending to ${recipientEmails.length} recipients...`);
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link href="/marketing" className="hover:text-blue-600">
          Marketing
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-700">Email Sequences</span>
      </nav>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Sequence List */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="font-semibold text-sm text-gray-500 uppercase tracking-wider">
            Sequences
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
                    {seq.status} &middot; {seq.sent_count}/{seq.recipient_count} sent
                  </div>
                </Link>
              ))}
              {(!sequencesData?.items || sequencesData.items.length === 0) && (
                <div className="p-3 text-center">
                  <p className="text-sm text-muted-foreground">No sequences yet.</p>
                  <p className="text-xs text-muted-foreground mt-1">Create one to get started.</p>
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
