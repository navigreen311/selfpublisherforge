"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  useCreateProofOrder,
  type ProofPlatform,
  type ProofOrderCreatePayload,
} from "../proofOrders";

interface OrderProofStepProps {
  publishingId?: string;
  bookId?: string;
  interiorFileUrl?: string;
  coverFileUrl?: string;
  onOrdered?: (orderId: string) => void;
  onSkip?: () => void;
}

const SHIPPING_OPTIONS = [
  { value: "standard", label: "Standard (5-8 business days) - $3.99", cost: 3.99 },
  { value: "expedited", label: "Expedited (3-5 business days) - $7.99", cost: 7.99 },
  { value: "priority", label: "Priority (1-2 business days) - $14.99", cost: 14.99 },
];

const PROOF_BASE_COST = 12.85;

/**
 * Step 3 of 5 in the publishing pipeline wizard: order a physical proof copy.
 *
 * Renders the form fields required by the spec:
 *   - quantity
 *   - platform (KDP / IngramSpark)
 *   - shipping address
 *   - billing
 *   - notes
 * Plus a "skip proof" escape hatch.
 */
export function OrderProofStep({
  publishingId,
  bookId,
  interiorFileUrl,
  coverFileUrl,
  onOrdered,
  onSkip,
}: OrderProofStepProps) {
  const router = useRouter();
  const createOrder = useCreateProofOrder();

  const [quantity, setQuantity] = useState(1);
  const [platform, setPlatform] = useState<ProofPlatform>("kdp");
  const [shippingMethod, setShippingMethod] = useState("standard");
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [stateCode, setStateCode] = useState("");
  const [zip, setZip] = useState("");
  const [billingMethod, setBillingMethod] = useState("card_on_file");
  const [billingRef, setBillingRef] = useState("");
  const [notes, setNotes] = useState("");
  const [skipConfirmed, setSkipConfirmed] = useState(false);

  const shipping =
    SHIPPING_OPTIONS.find((o) => o.value === shippingMethod) ?? SHIPPING_OPTIONS[0];
  const total = PROOF_BASE_COST * quantity + shipping.cost;

  const disabled =
    createOrder.isPending ||
    !name.trim() ||
    !address.trim() ||
    quantity < 1;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: ProofOrderCreatePayload = {
      publishing_id: publishingId,
      book_id: bookId,
      quantity,
      platform,
      shipping_method: shippingMethod,
      shipping_address: {
        name,
        address,
        city: city || undefined,
        state: stateCode || undefined,
        zip: zip || undefined,
      },
      billing: {
        method: billingMethod,
        reference: billingRef || undefined,
        amount: Number(total.toFixed(2)),
      },
      interior_file_url: interiorFileUrl,
      cover_file_url: coverFileUrl,
      notes: notes || undefined,
    };
    try {
      const result = await createOrder.mutateAsync(payload);
      if (onOrdered) onOrdered(result.id);
      else router.push(`/publishing/proof-orders/${result.id}`);
    } catch {
      /* toast handled in hook */
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-6">
      {/* Stepper */}
      <div>
        <h2 className="text-lg font-semibold">Step 3 of 5: Order Proof Copy</h2>
        <ol className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
          <li className="text-green-600">1. Metadata</li>
          <li className="text-green-600">2. Files</li>
          <li className="font-semibold text-indigo-600">3. Proof</li>
          <li>4. Review</li>
          <li>5. Publish</li>
        </ol>
      </div>

      <section className="rounded-md bg-muted/40 p-4 text-sm">
        <h3 className="font-medium">Why Order a Proof?</h3>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>Print quality and color accuracy</li>
          <li>Text readability at actual size</li>
          <li>Spine alignment and width</li>
          <li>Cover design as it appears in hand</li>
          <li>Page order and binding quality</li>
        </ul>
      </section>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="font-medium">Quantity</span>
            <input
              type="number"
              min={1}
              max={50}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium">Platform</span>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as ProofPlatform)}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
            >
              <option value="kdp">KDP</option>
              <option value="ingramspark">IngramSpark</option>
            </select>
          </label>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium">Shipping Address</legend>
          <input
            aria-label="Name"
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <input
            aria-label="Address"
            placeholder="Street address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <div className="grid gap-3 sm:grid-cols-3">
            <input
              aria-label="City"
              placeholder="City"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <input
              aria-label="State"
              placeholder="State"
              value={stateCode}
              onChange={(e) => setStateCode(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <input
              aria-label="ZIP"
              placeholder="ZIP"
              value={zip}
              onChange={(e) => setZip(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <label className="block text-sm">
            <span className="font-medium">Shipping method</span>
            <select
              value={shippingMethod}
              onChange={(e) => setShippingMethod(e.target.value)}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
            >
              {SHIPPING_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium">Billing</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              <span>Method</span>
              <select
                value={billingMethod}
                onChange={(e) => setBillingMethod(e.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              >
                <option value="card_on_file">Card on file</option>
                <option value="invoice">Invoice</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="block text-sm">
              <span>Reference</span>
              <input
                placeholder="PO # / reference (optional)"
                value={billingRef}
                onChange={(e) => setBillingRef(e.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </label>
          </div>
        </fieldset>

        <label className="block text-sm">
          <span className="font-medium">Notes</span>
          <textarea
            rows={3}
            placeholder="Anything the printer should know (optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
          />
        </label>

        <div className="flex items-center justify-between rounded-md bg-muted/40 px-4 py-3 text-sm">
          <span>Estimated total</span>
          <span className="font-semibold">${total.toFixed(2)}</span>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={disabled}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {createOrder.isPending ? "Placing order..." : "Order Proof Copy"}
          </button>
        </div>
      </form>

      <section className="border-t border-border pt-4">
        <h3 className="text-sm font-medium">OR Skip Proof</h3>
        <label className="mt-2 flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={skipConfirmed}
            onChange={(e) => setSkipConfirmed(e.target.checked)}
            className="mt-1"
          />
          <span>
            I&apos;m confident in my files and want to skip proof review.
            <span className="block text-amber-600">
              Not recommended - proof review catches ~40% of print issues.
            </span>
          </span>
        </label>
        <button
          type="button"
          disabled={!skipConfirmed}
          onClick={() => onSkip?.()}
          className="mt-3 rounded-md border border-border bg-background px-4 py-2 text-sm disabled:opacity-50"
        >
          Skip to Publish
        </button>
      </section>
    </div>
  );
}

export default OrderProofStep;
