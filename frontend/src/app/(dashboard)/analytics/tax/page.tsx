"use client";

import { TaxDashboardView } from "@/modules/tax/components/TaxDashboard";

export default function TaxPage() {
  return (
    <div className="space-y-4 px-4 sm:px-6 lg:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Tax</h1>
        <p className="text-muted-foreground">
          Year-to-date gross income, deductible expenses, and quarterly
          estimated tax payments.
        </p>
      </div>
      <TaxDashboardView />
    </div>
  );
}
