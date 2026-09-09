"use client";

import Link from "next/link";
import { useProofOrders } from "../proofOrders";

export function ProofOrdersTab() {
  const { data, isLoading, error } = useProofOrders();

  if (isLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading proof orders...</div>;
  }
  if (error) {
    return <div className="p-4 text-sm text-red-600">Failed to load proof orders.</div>;
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        <p>No proof orders yet.</p>
        <Link
          href="/publishing/proof-orders/new"
          className="mt-3 inline-block rounded-md bg-indigo-600 px-4 py-2 text-xs font-medium text-white hover:bg-indigo-700"
        >
          Order a Proof
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Proof Orders ({data?.total ?? items.length})</h3>
        <Link
          href="/publishing/proof-orders/new"
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
        >
          + New Proof
        </Link>
      </div>
      <ul className="divide-y divide-border rounded-md border border-border">
        {items.map((order) => (
          <li key={order.id}>
            <Link
              href={`/publishing/proof-orders/${order.id}`}
              className="flex items-center justify-between gap-4 p-3 text-sm hover:bg-muted/50"
            >
              <div>
                <div className="font-medium">#{order.id.slice(0, 8)}</div>
                <div className="text-xs text-muted-foreground">
                  {order.platform?.toUpperCase() ?? "-"} &middot; qty {order.quantity} &middot;{" "}
                  {new Date(order.ordered_at).toLocaleDateString()}
                </div>
              </div>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{order.status}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ProofOrdersTab;
