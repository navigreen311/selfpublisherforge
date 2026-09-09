"use client";

import { useSearchParams } from "next/navigation";
import { OrderProofStep } from "@/modules/publishing/components/OrderProofStep";

export default function NewProofOrderPage() {
  const params = useSearchParams();
  const publishingId = params.get("publishing_id") ?? undefined;
  const bookId = params.get("book_id") ?? undefined;

  return (
    <div className="space-y-6 px-4 sm:px-6 lg:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold">Order Proof Copy</h1>
        <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
          Step 3 of the publishing pipeline - verify print quality before going live.
        </p>
      </div>
      <OrderProofStep publishingId={publishingId} bookId={bookId} />
    </div>
  );
}
