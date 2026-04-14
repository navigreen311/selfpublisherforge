export type FilingStatus =
  | "single"
  | "married_joint"
  | "married_separate"
  | "head_of_household";

export interface TaxExpense {
  id: string;
  org_id: string;
  category: string;
  amount: string;
  description?: string | null;
  expense_date?: string | null;
  tax_year: number;
  receipt_url?: string | null;
  created_at: string;
}

export interface IncomeSourceRow {
  source: string;
  amount: string;
  expects_1099: boolean;
}

export interface QuarterlyEstimate {
  quarter: number;
  tax_year: number;
  label: string;
  due_date: string;
  estimated_amount: string;
  actual_amount?: string | null;
  paid: boolean;
  paid_date?: string | null;
}

export interface TaxDashboard {
  tax_year: number;
  filing_status: FilingStatus;
  tax_rate: string;
  gross_income: string;
  estimated_expenses: string;
  net_income: string;
  estimated_tax_owed: string;
  income_by_source: IncomeSourceRow[];
  quarterly_estimates: QuarterlyEstimate[];
  next_quarterly_due?: string | null;
  disclaimer: string;
}

export interface TaxExpenseInput {
  category: string;
  amount: string;
  description?: string;
  expense_date?: string;
  tax_year: number;
  receipt_url?: string;
}
