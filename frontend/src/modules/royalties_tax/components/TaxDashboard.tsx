"use client";

import { useMemo, useState } from "react";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import {
  downloadTaxDocument,
  useGenerateTaxDocument,
  usePlatformBreakdown,
  useRoyaltySummary,
  useTaxDocuments,
} from "../hooks";

function formatCurrency(value: number | string | null | undefined) {
  const num = Number(value ?? 0);
  return `$${num.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function KpiCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${accent ?? "text-gray-900"}`}>{value}</p>
    </div>
  );
}

export function TaxDashboard() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [taxRate, setTaxRate] = useState(25);

  const summary = useRoyaltySummary(year, "ytd");
  const platforms = usePlatformBreakdown(year);
  const docs = useTaxDocuments(year);
  const generate = useGenerateTaxDocument();

  const gross = Number(summary.data?.ytd_earnings ?? 0);
  // Placeholder expenses until a full expenses UI is built.
  const expenses = 0;
  const net = gross - expenses;
  const estTax = (net * taxRate) / 100;

  const quarters = useMemo(() => {
    const quarterly = estTax / 4;
    return [
      { label: "Q1 (Jan–Mar)", due: `Apr 15, ${year}`, amount: quarterly },
      { label: "Q2 (Apr–Jun)", due: `Jun 15, ${year}`, amount: quarterly },
      { label: "Q3 (Jul–Sep)", due: `Sep 15, ${year}`, amount: quarterly },
      { label: "Q4 (Oct–Dec)", due: `Jan 15, ${year + 1}`, amount: quarterly },
    ];
  }, [estTax, year]);

  const hasData = gross > 0 || (docs.data?.items?.length ?? 0) > 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Tax Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Income, expense, and estimated quarterly tax tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            aria-label="Tax year"
          >
            {[0, 1, 2, 3].map((offset) => {
              const y = currentYear - offset;
              return (
                <option key={y} value={y}>
                  {y}
                </option>
              );
            })}
          </select>
          <Button
            onClick={() =>
              generate.mutate({
                tax_year: year,
                document_type: "year_end_summary",
                format: "pdf",
              })
            }
            disabled={generate.isPending}
          >
            {generate.isPending ? "Generating…" : "Generate Year-End Summary"}
          </Button>
        </div>
      </div>

      {summary.isError ? (
        <ErrorState
          message={summary.error?.message ?? "Failed to load tax summary"}
          onRetry={() => summary.refetch()}
        />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <KpiCard label="Gross Income" value={formatCurrency(gross)} accent="text-blue-600" />
          <KpiCard
            label="Estimated Expenses"
            value={formatCurrency(expenses)}
            accent="text-gray-700"
          />
          <KpiCard
            label="Est. Tax Owed"
            value={formatCurrency(estTax)}
            accent="text-red-600"
          />
          <KpiCard label="Next Quarterly" value={quarters[0]?.due ?? "—"} />
        </div>
      )}

      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold">Income by Source</h3>
        {platforms.isError ? (
          <ErrorState
            message={platforms.error?.message ?? "Failed to load sources"}
            onRetry={() => platforms.refetch()}
          />
        ) : (platforms.data?.entries?.length ?? 0) === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No income recorded for {year} yet.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
              <tr>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2 text-right">YTD Amount</th>
                <th className="px-3 py-2">1099 Expected?</th>
              </tr>
            </thead>
            <tbody>
              {platforms.data!.entries.map((p) => {
                const amount = Number(p.amount);
                return (
                  <tr key={p.platform} className="border-t">
                    <td className="px-3 py-2 font-medium capitalize">{p.platform}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(amount)}</td>
                    <td className="px-3 py-2">
                      {amount >= 600 ? (
                        <span className="text-green-700">Yes (over $600)</span>
                      ) : (
                        <span className="text-gray-500">No (under $600)</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              <tr className="border-t bg-gray-50 font-semibold">
                <td className="px-3 py-2">Total Gross Income</td>
                <td className="px-3 py-2 text-right">{formatCurrency(gross)}</td>
                <td className="px-3 py-2" />
              </tr>
            </tbody>
          </table>
        )}
      </div>

      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold">Estimated Quarterly Tax Payments</h3>
        <div className="mb-3 flex items-center gap-3 text-sm">
          <label className="font-medium">Tax Rate:</label>
          <select
            value={taxRate}
            onChange={(e) => setTaxRate(Number(e.target.value))}
            className="rounded-md border px-2 py-1"
          >
            {[15, 20, 22, 24, 25, 28, 32].map((r) => (
              <option key={r} value={r}>
                {r}%
              </option>
            ))}
          </select>
        </div>
        <ul className="space-y-1 text-sm">
          {quarters.map((q) => (
            <li key={q.label} className="flex items-center justify-between border-b py-1">
              <span>{q.label}</span>
              <span>Due: {q.due}</span>
              <span className="font-medium">{formatCurrency(q.amount)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-muted-foreground">
          This is an estimate only. Consult a tax professional for accurate tax advice.
          SelfPublisherForge is not a tax advisor.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold">Tax Documents</h3>
        {docs.isError ? (
          <ErrorState
            message={docs.error?.message ?? "Failed to load documents"}
            onRetry={() => docs.refetch()}
          />
        ) : !hasData && (docs.data?.items?.length ?? 0) === 0 ? (
          <EmptyState
            icon={<FileText className="h-10 w-10" aria-hidden />}
            title="No tax documents generated yet"
            description="Generate year-end summaries, 1099 breakdowns, and tax-preparer CSVs once you've imported royalty data."
            actionLabel="Generate Year-End Summary"
            onAction={() =>
              generate.mutate({
                tax_year: year,
                document_type: "year_end_summary",
                format: "pdf",
              })
            }
          />
        ) : (docs.data?.items?.length ?? 0) === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No documents for {year} yet.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
              <tr>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Format</th>
                <th className="px-3 py-2">Generated</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.data!.items.map((d) => (
                <tr key={d.id} className="border-t">
                  <td className="px-3 py-2">{d.title}</td>
                  <td className="px-3 py-2">{d.document_type}</td>
                  <td className="px-3 py-2 uppercase">{d.format}</td>
                  <td className="px-3 py-2">
                    {new Date(d.generated_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        downloadTaxDocument(
                          d.id,
                          `${d.title}.${d.format === "csv" ? "csv" : "txt"}`
                        )
                      }
                    >
                      Download
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
