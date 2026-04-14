"use client";

import {
  useProofOrder,
  useUpdateProofOrderStatus,
  type ProofOrderStatus,
} from "../proofOrders";

const STATUS_STEPS: { value: ProofOrderStatus; label: string }[] = [
  { value: "ordered", label: "Ordered" },
  { value: "processing", label: "Processing" },
  { value: "printed", label: "Printed" },
  { value: "shipped", label: "Shipped" },
  { value: "delivered", label: "Delivered" },
  { value: "reviewed", label: "Reviewed" },
  { value: "approved", label: "Approved" },
];

function stepIndex(status: ProofOrderStatus): number {
  const idx = STATUS_STEPS.findIndex((s) => s.value === status);
  return idx >= 0 ? idx : 0;
}

interface ProofOrderTrackerProps {
  orderId: string;
}

export function ProofOrderTracker({ orderId }: ProofOrderTrackerProps) {
  const { data: order, isLoading, error } = useProofOrder(orderId);
  const updateStatus = useUpdateProofOrderStatus(orderId);

  if (isLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading proof order...</div>;
  }
  if (error || !order) {
    return (
      <div className="p-6 text-sm text-red-600">
        Failed to load proof order.
      </div>
    );
  }

  const current = stepIndex(order.status);

  return (
    <div className="space-y-6 rounded-lg border border-border bg-card p-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Proof Order Status</h2>
          <p className="text-xs text-muted-foreground">
            Order #{order.id.slice(0, 8)} &middot; Platform:{" "}
            {order.platform?.toUpperCase() ?? "-"}
          </p>
        </div>
        <span className="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">
          {order.status}
        </span>
      </header>

      {/* Status tracker */}
      <ol className="flex flex-wrap items-center gap-2 text-xs">
        {STATUS_STEPS.map((step, i) => {
          const reached = i <= current;
          return (
            <li
              key={step.value}
              className={`flex items-center gap-2 rounded-full px-3 py-1 ${
                reached
                  ? "bg-indigo-600 text-white"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <span className="font-mono">{i + 1}</span>
              <span>{step.label}</span>
            </li>
          );
        })}
      </ol>

      {/* Details */}
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">Quantity</dt>
          <dd>{order.quantity}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Shipping to</dt>
          <dd>
            {order.shipping_name}
            <br />
            {order.shipping_address}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Shipping method</dt>
          <dd>{order.shipping_method ?? "-"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Tracking</dt>
          <dd>{order.tracking_number ?? "Not yet available"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Estimated delivery</dt>
          <dd>{order.estimated_delivery ?? "TBD"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Ordered at</dt>
          <dd>{new Date(order.ordered_at).toLocaleString()}</dd>
        </div>
      </dl>

      {order.notes && (
        <div className="rounded-md bg-muted/40 p-3 text-sm">
          <span className="font-medium">Notes: </span>
          {order.notes}
        </div>
      )}

      {/* Status actions */}
      <div className="flex flex-wrap gap-2 border-t border-border pt-4">
        {(
          [
            "processing",
            "printed",
            "shipped",
            "delivered",
            "reviewed",
            "approved",
            "rejected",
            "cancelled",
          ] as ProofOrderStatus[]
        ).map((s) => (
          <button
            key={s}
            type="button"
            disabled={updateStatus.isPending || order.status === s}
            onClick={() => updateStatus.mutate({ status: s })}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
          >
            Mark {s}
          </button>
        ))}
      </div>
    </div>
  );
}

export default ProofOrderTracker;
