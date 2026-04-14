"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useTaxDashboard,
  useTaxExpenses,
  useCreateExpense,
  useDeleteExpense,
  useMarkQuarterlyPaid,
  downloadTaxExport,
} from "../hooks";
import { TaxDisclaimer } from "./TaxDisclaimer";
import type { FilingStatus } from "../types";

const YEARS = [2024, 2025, 2026, 2027];
const TAX_RATES = ["0.15", "0.20", "0.25", "0.30", "0.35"];
const STATUSES: { value: FilingStatus; label: string }[] = [
  { value: "single", label: "Single" },
  { value: "married_joint", label: "Married, joint" },
  { value: "married_separate", label: "Married, separate" },
  { value: "head_of_household", label: "Head of household" },
];

const EXPENSE_CATEGORIES = [
  "AI Services",
  "Software/Tools",
  "Advertising",
  "Stock Photos",
  "ISBN Purchase",
  "Proof Copies",
  "Education",
  "Editing",
  "Cover Design",
  "Other",
];

export function TaxDashboardView() {
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [taxRate, setTaxRate] = useState<string>("0.25");
  const [filingStatus, setFilingStatus] = useState<FilingStatus>("single");

  const { data: dashboard, isLoading } = useTaxDashboard(year, taxRate, filingStatus);
  const { data: expenses } = useTaxExpenses(year);
  const createExpense = useCreateExpense();
  const deleteExpense = useDeleteExpense();
  const markPaid = useMarkQuarterlyPaid();

  const [newCat, setNewCat] = useState(EXPENSE_CATEGORIES[0]);
  const [newAmt, setNewAmt] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const addExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAmt) return;
    await createExpense.mutateAsync({
      category: newCat,
      amount: newAmt,
      description: newDesc || undefined,
      expense_date: newDate || undefined,
      tax_year: year,
    });
    setNewAmt("");
    setNewDesc("");
    setNewDate("");
  };

  if (isLoading || !dashboard) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <TaxDisclaimer />

      <div className="flex flex-wrap gap-3 items-center">
        <label className="text-sm">
          Year
          <select
            className="ml-2 rounded border px-2 py-1"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {YEARS.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Tax Rate
          <select
            className="ml-2 rounded border px-2 py-1"
            value={taxRate}
            onChange={(e) => setTaxRate(e.target.value)}
          >
            {TAX_RATES.map((r) => (
              <option key={r} value={r}>
                {(Number(r) * 100).toFixed(0)}%
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Filing Status
          <select
            className="ml-2 rounded border px-2 py-1"
            value={filingStatus}
            onChange={(e) => setFilingStatus(e.target.value as FilingStatus)}
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Gross Income" value={`$${dashboard.gross_income}`} />
        <KpiCard label="Expenses" value={`$${dashboard.estimated_expenses}`} />
        <KpiCard label="Est. Tax Owed" value={`$${dashboard.estimated_tax_owed}`} />
        <KpiCard
          label="Next Quarterly"
          value={dashboard.next_quarterly_due ?? "—"}
        />
      </div>

      {/* Income by source */}
      <Card>
        <CardHeader>
          <CardTitle>Income by Source</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Source</th>
                <th className="py-2 text-right">YTD Amount</th>
                <th className="py-2 text-right">1099 Expected?</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.income_by_source.map((r) => (
                <tr key={r.source} className="border-t">
                  <td className="py-2">{r.source}</td>
                  <td className="py-2 text-right font-mono">${r.amount}</td>
                  <td className="py-2 text-right">
                    {r.expects_1099 ? "Yes (>$600)" : "No (<$600)"}
                  </td>
                </tr>
              ))}
              <tr className="border-t-2 font-semibold">
                <td className="py-2">Total Gross</td>
                <td className="py-2 text-right font-mono">
                  ${dashboard.gross_income}
                </td>
                <td />
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Expenses */}
      <Card>
        <CardHeader>
          <CardTitle>Deductible Expenses</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={addExpense} className="grid md:grid-cols-5 gap-2">
            <select
              value={newCat}
              onChange={(e) => setNewCat(e.target.value)}
              className="rounded border px-2 py-1 text-sm"
            >
              {EXPENSE_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <Input
              type="number"
              step="0.01"
              placeholder="Amount"
              value={newAmt}
              onChange={(e) => setNewAmt(e.target.value)}
            />
            <Input
              type="date"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
            />
            <Input
              placeholder="Description"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
            />
            <Button type="submit" size="sm" disabled={createExpense.isPending}>
              Add Expense
            </Button>
          </form>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Category</th>
                <th className="py-2 text-right">Amount</th>
                <th className="py-2">Date</th>
                <th className="py-2">Notes</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {(expenses ?? []).map((e) => (
                <tr key={e.id} className="border-t">
                  <td className="py-2">{e.category}</td>
                  <td className="py-2 text-right font-mono">${e.amount}</td>
                  <td className="py-2">{e.expense_date ?? "—"}</td>
                  <td className="py-2">{e.description ?? ""}</td>
                  <td className="py-2 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteExpense.mutate(e.id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
              <tr className="border-t-2 font-semibold">
                <td className="py-2">Total</td>
                <td className="py-2 text-right font-mono">
                  ${dashboard.estimated_expenses}
                </td>
                <td colSpan={3} />
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Quarterly */}
      <Card>
        <CardHeader>
          <CardTitle>Estimated Quarterly Tax Payments</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground mb-3">
            Based on: Net income × estimated tax rate ({(Number(taxRate) * 100).toFixed(0)}%).
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Quarter</th>
                <th className="py-2 text-right">Estimated</th>
                <th className="py-2">Due</th>
                <th className="py-2">Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {dashboard.quarterly_estimates.map((q) => (
                <tr key={q.quarter} className="border-t">
                  <td className="py-2">{q.label}</td>
                  <td className="py-2 text-right font-mono">
                    ${q.estimated_amount}
                  </td>
                  <td className="py-2">{q.due_date}</td>
                  <td className="py-2">
                    {q.paid ? `Paid ${q.paid_date ?? ""}` : "Unpaid"}
                  </td>
                  <td className="py-2 text-right">
                    {!q.paid && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          markPaid.mutate({
                            year,
                            quarter: q.quarter,
                            paid: true,
                          })
                        }
                      >
                        Mark Paid
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={() => downloadTaxExport("pdf", year, taxRate, filingStatus)}
        >
          Export Year-End Summary (PDF)
        </Button>
        <Button
          variant="outline"
          onClick={() => downloadTaxExport("csv", year, taxRate, filingStatus)}
        >
          Export for Tax Preparer (CSV)
        </Button>
      </div>

      <TaxDisclaimer />
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wide">
          {label}
        </div>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}
