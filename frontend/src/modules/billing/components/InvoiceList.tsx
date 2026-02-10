"use client";

import type { InvoiceItem } from "../hooks";

interface InvoiceListProps {
  invoices: InvoiceItem[];
  isLoading?: boolean;
}

/**
 * Displays a table of past invoices with download / view links.
 */
export function InvoiceList({ invoices, isLoading = false }: InvoiceListProps) {
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 rounded-lg bg-gray-100" />
        ))}
      </div>
    );
  }

  if (invoices.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No invoices found. Invoices will appear here after your first payment.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Invoice
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Date
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Amount
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {invoices.map((invoice) => (
            <tr key={invoice.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                {invoice.number || invoice.id}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {new Date(invoice.created).toLocaleDateString()}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                ${(invoice.amount_due / 100).toFixed(2)}{" "}
                <span className="uppercase text-gray-400">
                  {invoice.currency}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm">
                <InvoiceStatusBadge status={invoice.status} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                <div className="flex items-center justify-end gap-2">
                  {invoice.hosted_invoice_url && (
                    <a
                      href={invoice.hosted_invoice_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      View
                    </a>
                  )}
                  {invoice.invoice_pdf && (
                    <a
                      href={invoice.invoice_pdf}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      PDF
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function InvoiceStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    paid: "bg-green-100 text-green-800",
    open: "bg-blue-100 text-blue-800",
    draft: "bg-gray-100 text-gray-800",
    void: "bg-gray-100 text-gray-500",
    uncollectible: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[status] || "bg-gray-100 text-gray-800"
      }`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
