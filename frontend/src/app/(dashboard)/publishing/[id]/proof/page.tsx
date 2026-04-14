"use client";

import { useParams, useRouter } from "next/navigation";
import { ProofOrderStep } from "@/modules/proof-orders/components/ProofOrderStep";

export default function PublishingProofPage() {
  const params = useParams();
  const router = useRouter();
  const publishingId = String(params?.id ?? "");

  return (
    <div className="space-y-4 px-4 sm:px-6 lg:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
          Step 3 of 5: Order Proof Copy
        </h1>
        <p className="text-muted-foreground">
          Order and review a physical proof copy before publishing.
        </p>
      </div>
      {publishingId && (
        <ProofOrderStep
          publishingId={publishingId}
          onApproved={() => router.push(`/publishing`)}
        />
      )}
    </div>
  );
}
