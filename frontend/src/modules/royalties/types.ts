export type Distributor = "kdp" | "ingram" | "d2d" | "other";

export interface RoyaltyEntry {
  id: string;
  org_id: string;
  distributor: string;
  royalty_type: string;
  amount: string;
  currency: string;
  units_sold?: number | null;
  kenp_pages?: number | null;
  royalty_rate?: string | null;
  period_month?: number | null;
  period_year?: number | null;
  payment_date?: string | null;
  book_id?: string | null;
  pen_name_id?: string | null;
  source: string;
  import_batch_id?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface DistributorSummary {
  distributor: string;
  total: string;
  pct: number;
  breakdown: Record<string, string>;
  units_sold: number;
  kenp_pages: number;
  last_payment_amount?: string | null;
  last_payment_date?: string | null;
}

export interface RoyaltyDashboard {
  ytd_earnings: string;
  this_month_earnings: string;
  pending_payout: string;
  next_payout_date?: string | null;
  by_distributor: DistributorSummary[];
  total: string;
  period: string;
  year: number;
}

export interface MonthlyStatementRow {
  month: number;
  year: number;
  label: string;
  kdp_ebook: string;
  kdp_print: string;
  ku_kenp: string;
  ingram: string;
  d2d: string;
  other: string;
  total: string;
}

export interface MonthlyStatement {
  year: number;
  rows: MonthlyStatementRow[];
  ytd_totals: MonthlyStatementRow;
}

export interface RoyaltyImportResult {
  imported: number;
  skipped: number;
  distributor: string;
  import_batch_id: string;
  errors: string[];
  total_amount: string;
}

export interface ManualEntryInput {
  distributor: string;
  royalty_type: string;
  amount: string;
  currency?: string;
  period_month?: number;
  period_year?: number;
  payment_date?: string;
  book_id?: string;
  pen_name_id?: string;
  notes?: string;
}

export const DISTRIBUTOR_LABELS: Record<string, string> = {
  kdp: "Amazon KDP",
  ingram: "IngramSpark",
  d2d: "Draft2Digital",
  other: "Other",
};
