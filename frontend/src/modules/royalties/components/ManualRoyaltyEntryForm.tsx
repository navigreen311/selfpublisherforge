"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useManualRoyaltyEntry } from "../hooks";

const ROYALTY_TYPES = [
  "kindle_ebook",
  "ku_kenp",
  "paperback",
  "hardcover",
  "ebook",
  "print",
  "other",
];

export function ManualRoyaltyEntryForm({ defaultYear }: { defaultYear: number }) {
  const [distributor, setDistributor] = useState("kdp");
  const [type, setType] = useState("kindle_ebook");
  const [amount, setAmount] = useState("");
  const [month, setMonth] = useState<number>(new Date().getMonth() + 1);
  const [year, setYear] = useState<number>(defaultYear);
  const [notes, setNotes] = useState("");
  const mut = useManualRoyaltyEntry();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount) return;
    await mut.mutateAsync({
      distributor,
      royalty_type: type,
      amount,
      period_month: month,
      period_year: year,
      notes: notes || undefined,
    });
    setAmount("");
    setNotes("");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Manual Royalty Entry</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-sm">
              Distributor
              <select
                value={distributor}
                onChange={(e) => setDistributor(e.target.value)}
                className="mt-1 w-full rounded border px-2 py-1"
              >
                <option value="kdp">Amazon KDP</option>
                <option value="ingram">IngramSpark</option>
                <option value="d2d">Draft2Digital</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="block text-sm">
              Type
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="mt-1 w-full rounded border px-2 py-1"
              >
                {ROYALTY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <label className="block text-sm">
              Amount (USD)
              <Input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="125.50"
                required
              />
            </label>
            <label className="block text-sm">
              Month
              <Input
                type="number"
                min={1}
                max={12}
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
              />
            </label>
            <label className="block text-sm">
              Year
              <Input
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
              />
            </label>
          </div>
          <label className="block text-sm">
            Notes
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional"
            />
          </label>
          <Button type="submit" disabled={mut.isPending} size="sm">
            {mut.isPending ? "Saving..." : "Add Entry"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
