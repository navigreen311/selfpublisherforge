"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  useOrderProof,
  useProofCostEstimate,
  useProofReview,
  useProofStatus,
  useSkipProof,
} from "../hooks";
import {
  CHECKLIST_ITEMS,
  Checklist,
  IssuesLevel,
  ShippingMethod,
} from "../types";

const INTERIOR_TYPES = [
  { value: "black_white", label: "Black & White" },
  { value: "standard_color", label: "Standard Color" },
  { value: "premium_color", label: "Premium Color" },
];
const SHIPPING_METHODS: { value: ShippingMethod; label: string }[] = [
  { value: "standard", label: "Standard (5-8 business days)" },
  { value: "expedited", label: "Expedited (3-5 business days)" },
  { value: "priority", label: "Priority (1-2 business days)" },
];

export interface ProofOrderStepProps {
  publishingId: string;
  interiorFileUrl?: string;
  coverFileUrl?: string;
  trimSize?: string;
  pageCount?: number;
  interiorType?: string;
  onApproved?: () => void;
}

export function ProofOrderStep(props: ProofOrderStepProps) {
  const { publishingId, onApproved } = props;
  const { data: order, isLoading } = useProofStatus(publishingId);
  const orderMut = useOrderProof(publishingId);
  const skipMut = useSkipProof(publishingId);

  if (isLoading) return <div>Loading...</div>;

  if (!order) {
    return (
      <OrderForm
        {...props}
        onOrder={(payload) => orderMut.mutate(payload)}
        onSkip={() => skipMut.mutate({ reason: "Skipped by author" })}
        isPending={orderMut.isPending || skipMut.isPending}
      />
    );
  }

  if (order.skipped) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Proof Skipped</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Proof review was skipped. Publishing may proceed.
        </CardContent>
      </Card>
    );
  }

  return (
    <ReviewPanel
      publishingId={publishingId}
      order={order}
      onApproved={onApproved}
    />
  );
}

// ---------------------------------------------------------------------------
// Order form (pre-order state)
// ---------------------------------------------------------------------------

function OrderForm({
  publishingId: _publishingId,
  interiorFileUrl: fileUrl = "",
  coverFileUrl: coverUrl = "",
  trimSize = "6x9",
  pageCount: initialPages = 200,
  interiorType: initialInterior = "black_white",
  onOrder,
  onSkip,
  isPending,
}: ProofOrderStepProps & {
  onOrder: (p: any) => void;
  onSkip: () => void;
  isPending: boolean;
}) {
  const [interiorFile, setInteriorFile] = useState(fileUrl);
  const [coverFile, setCoverFile] = useState(coverUrl);
  const [pages, setPages] = useState<number>(initialPages);
  const [itype, setItype] = useState(initialInterior);
  const [method, setMethod] = useState<ShippingMethod>("standard");
  const [addr, setAddr] = useState({
    name: "",
    address: "",
    city: "",
    state: "",
    zip: "",
  });
  const [confirmSkip, setConfirmSkip] = useState(false);

  const { data: estimate } = useProofCostEstimate(pages, itype, method, pages > 0);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onOrder({
      interior_file_url: interiorFile,
      cover_file_url: coverFile,
      trim_size: trimSize,
      page_count: pages,
      interior_type: itype,
      shipping_address: addr,
      shipping_method: method,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Order Proof Copy</CardTitle>
      </CardHeader>
      <CardContent>
        <section className="space-y-2 mb-4 text-sm">
          <h3 className="font-semibold">Why Order a Proof?</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li>Print quality and color accuracy</li>
            <li>Text readability at actual size</li>
            <li>Spine text alignment and width</li>
            <li>Cover design as it appears in hand</li>
            <li>Page order and binding quality</li>
          </ul>
        </section>
        <form onSubmit={submit} className="space-y-3 text-sm">
          <div className="grid md:grid-cols-2 gap-2">
            <label>
              Interior PDF URL
              <Input
                value={interiorFile}
                onChange={(e) => setInteriorFile(e.target.value)}
                required
              />
            </label>
            <label>
              Cover PDF URL
              <Input
                value={coverFile}
                onChange={(e) => setCoverFile(e.target.value)}
                required
              />
            </label>
            <label>
              Page Count
              <Input
                type="number"
                min={24}
                max={828}
                value={pages}
                onChange={(e) => setPages(Number(e.target.value))}
              />
            </label>
            <label>
              Interior
              <select
                value={itype}
                onChange={(e) => setItype(e.target.value)}
                className="mt-1 w-full rounded border px-2 py-1"
              >
                {INTERIOR_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="md:col-span-2">
              Shipping Method
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as ShippingMethod)}
                className="mt-1 w-full rounded border px-2 py-1"
              >
                {SHIPPING_METHODS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <fieldset className="border rounded p-3 space-y-2">
            <legend className="text-sm font-semibold px-1">Ship to</legend>
            <Input
              placeholder="Name"
              value={addr.name}
              onChange={(e) => setAddr({ ...addr, name: e.target.value })}
              required
            />
            <Input
              placeholder="Address"
              value={addr.address}
              onChange={(e) => setAddr({ ...addr, address: e.target.value })}
              required
            />
            <div className="grid grid-cols-3 gap-2">
              <Input
                placeholder="City"
                value={addr.city}
                onChange={(e) => setAddr({ ...addr, city: e.target.value })}
                required
              />
              <Input
                placeholder="State"
                maxLength={2}
                value={addr.state}
                onChange={(e) => setAddr({ ...addr, state: e.target.value })}
                required
              />
              <Input
                placeholder="ZIP"
                value={addr.zip}
                onChange={(e) => setAddr({ ...addr, zip: e.target.value })}
                required
              />
            </div>
          </fieldset>

          {estimate && (
            <div className="text-sm bg-muted/50 p-2 rounded">
              Proof cost: ${estimate.print_cost} + Shipping $
              {estimate.shipping_cost} = <b>Total ${estimate.total}</b>
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={isPending}>
              {isPending ? "Ordering..." : "Order Proof Copy"}
            </Button>
          </div>
        </form>

        <section className="mt-6 pt-4 border-t space-y-2">
          <h3 className="text-sm font-semibold">Or Skip Proof</h3>
          <label className="flex items-start gap-2 text-sm">
            <Checkbox
              checked={confirmSkip}
              onCheckedChange={(v) => setConfirmSkip(Boolean(v))}
            />
            <span>
              I&apos;m confident in my files and want to skip proof review.
              Not recommended — proof review catches ~40% of print issues.
            </span>
          </label>
          <Button
            variant="outline"
            size="sm"
            disabled={!confirmSkip || isPending}
            onClick={onSkip}
          >
            Skip to Publish →
          </Button>
        </section>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Review panel (post-order state)
// ---------------------------------------------------------------------------

function ReviewPanel({
  publishingId,
  order,
  onApproved,
}: {
  publishingId: string;
  order: any;
  onApproved?: () => void;
}) {
  const [checklist, setChecklist] = useState<Checklist>(() => ({
    print_quality: Boolean(order.checklist?.print_quality),
    colors: Boolean(order.checklist?.colors),
    text: Boolean(order.checklist?.text),
    pages: Boolean(order.checklist?.pages),
    cover: Boolean(order.checklist?.cover),
    spine: Boolean(order.checklist?.spine),
    barcode: Boolean(order.checklist?.barcode),
    overall: Boolean(order.checklist?.overall),
  }));
  const [issues, setIssues] = useState<IssuesLevel>(
    (order.issues as IssuesLevel) || "none",
  );
  const [notes, setNotes] = useState<string>(order.notes || "");
  const review = useProofReview(publishingId);

  const allChecked = CHECKLIST_ITEMS.every((i) => checklist[i.key]);
  const canApprove = allChecked && issues !== "major";

  const save = async (approved: boolean) => {
    const res = await review.mutateAsync({
      checklist,
      issues,
      notes: notes || undefined,
      approved,
    });
    if (approved && onApproved) onApproved();
    return res;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Proof Review</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm space-y-1">
          <div>
            Status: <b>{order.status}</b>
          </div>
          {order.tracking_number && (
            <div>
              Tracking:{" "}
              <span className="font-mono">{order.tracking_number}</span>
            </div>
          )}
          {order.estimated_delivery && (
            <div>Estimated delivery: {order.estimated_delivery}</div>
          )}
          {order.cost && <div>Total cost: ${order.cost}</div>}
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-semibold">Review Checklist</legend>
          {CHECKLIST_ITEMS.map((item) => (
            <label key={item.key} className="flex items-start gap-2 text-sm">
              <Checkbox
                checked={checklist[item.key]}
                onCheckedChange={(v) =>
                  setChecklist({ ...checklist, [item.key]: Boolean(v) })
                }
              />
              <span>{item.label}</span>
            </label>
          ))}
        </fieldset>

        <fieldset className="space-y-1">
          <legend className="text-sm font-semibold">Issues</legend>
          {(["none", "minor", "major"] as IssuesLevel[]).map((v) => (
            <label key={v} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="issues"
                checked={issues === v}
                onChange={() => setIssues(v)}
              />
              <span>
                {v === "none"
                  ? "No issues"
                  : v === "minor"
                  ? "Minor issues — fixing and re-uploading"
                  : "Major issues — need to re-do interior/cover"}
              </span>
            </label>
          ))}
        </fieldset>

        <label className="block text-sm">
          Notes
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes about the proof"
          />
        </label>

        <div className="flex gap-2 items-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => save(false)}
            disabled={review.isPending}
          >
            Save Checklist
          </Button>
          <Button
            size="sm"
            disabled={!canApprove || review.isPending}
            onClick={() => save(true)}
          >
            Proof Approved — Proceed to Publish
          </Button>
          {!canApprove && (
            <span className="text-xs text-muted-foreground">
              {allChecked ? "Resolve major issues first." : "Check all items to approve."}
            </span>
          )}
        </div>

        {order.approved && (
          <div className="text-sm text-green-600 font-medium">
            ✓ Approved on {order.approved_at}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
