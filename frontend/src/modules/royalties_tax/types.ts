export interface RoyaltySummary {
  ytd_earnings: number | string;
  month_earnings: number | string;
  pending_payout: number | string;
  next_payout_date: string | null;
  period: string;
  year: number;
  currency: string;
}

export interface RoyaltyRecord {
  id: string;
  book_id: string | null;
  platform: string;
  title: string | null;
  format_type: string | null;
  units_sold: number;
  royalty_rate: number | string | null;
  gross_revenue: number | string;
  net_revenue: number | string;
  currency: string;
  period_start: string | null;
  period_end: string | null;
}

export interface RoyaltyRecordList {
  items: RoyaltyRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface PlatformBreakdownEntry {
  platform: string;
  amount: number | string;
  percentage: number;
  units_sold: number;
  last_payment_amount: number | string | null;
  last_payment_date: string | null;
  royalty_rate: number | string | null;
}

export interface PlatformBreakdown {
  total: number | string;
  currency: string;
  entries: PlatformBreakdownEntry[];
}

export interface BookBreakdownEntry {
  book_id: string | null;
  title: string;
  units_sold: number;
  gross_revenue: number | string;
  net_revenue: number | string;
  platforms: string[];
}

export interface BookBreakdown {
  total: number | string;
  entries: BookBreakdownEntry[];
}

export interface RoyaltyImportResult {
  id: string;
  platform: string;
  status: string;
  source_filename: string | null;
  records_processed: number;
  records_failed: number;
  total_amount: number | string | null;
  currency: string;
  imported_at: string;
}

export interface TaxDocument {
  id: string;
  tax_year: number;
  document_type: string;
  platform: string | null;
  title: string;
  status: string;
  format: string;
  gross_income: number | string | null;
  total_expenses: number | string | null;
  estimated_tax: number | string | null;
  file_size_bytes: number | null;
  generated_at: string;
}

export interface TaxDocumentList {
  items: TaxDocument[];
  total: number;
}
