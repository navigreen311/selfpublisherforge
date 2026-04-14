"use client";

import { useParams } from "next/navigation";
import { ProofOrderTracker } from "@/modules/publishing/components/ProofOrderTracker";

export default function ProofOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const id = typeof params?.id === "string" ? params.id : "";

  return (
    <div className="space-y-6 px-4 sm:px-6 lg:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold">Proof Order</h1>
        <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
          Track your proof copy through printing, shipping, and review.
        </p>
      </div>
      {id ? (
        <ProofOrderTracker orderId={id} />
      ) : (
        <p className="text-sm text-red-600">Missing order id.</p>
      )}
    </div>
  );
}
