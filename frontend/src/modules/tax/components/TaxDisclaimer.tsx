"use client";

import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export const TAX_DISCLAIMER_TEXT =
  "This is an estimate only. Consult a tax professional for accurate tax advice. SelfPublisherForge is not a tax advisor.";

/**
 * REQUIRED on every tax-related page. Do not hide or remove.
 */
export function TaxDisclaimer({ className }: { className?: string }) {
  return (
    <Alert className={className} variant="default" role="alert" aria-live="polite">
      <AlertTriangle className="h-4 w-4" aria-hidden="true" />
      <AlertDescription>{TAX_DISCLAIMER_TEXT}</AlertDescription>
    </Alert>
  );
}
