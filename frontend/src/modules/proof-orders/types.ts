export type ShippingMethod = "standard" | "expedited" | "priority";
export type IssuesLevel = "none" | "minor" | "major";

export interface ShippingAddress {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

export interface Checklist {
  print_quality: boolean;
  colors: boolean;
  text: boolean;
  pages: boolean;
  cover: boolean;
  spine: boolean;
  barcode: boolean;
  overall: boolean;
}

export const CHECKLIST_ITEMS: { key: keyof Checklist; label: string }[] = [
  { key: "print_quality", label: "Print quality is acceptable" },
  { key: "colors", label: "Colors match expectations" },
  { key: "text", label: "Text is readable at printed size" },
  { key: "pages", label: "No missing or misordered pages" },
  { key: "cover", label: "Cover looks correct (front, spine, back)" },
  { key: "spine", label: "Spine text is centered and readable" },
  { key: "barcode", label: "Barcode/ISBN prints correctly" },
  { key: "overall", label: "Overall quality is ready for sale" },
];

export interface ProofOrder {
  id: string;
  org_id: string;
  publishing_id: string;
  book_id?: string | null;
  interior_file_url: string;
  cover_file_url: string;
  trim_size?: string | null;
  page_count?: number | null;
  interior_type?: string | null;
  shipping_name?: string | null;
  shipping_address?: string | null;
  shipping_city?: string | null;
  shipping_state?: string | null;
  shipping_zip?: string | null;
  shipping_method?: string | null;
  print_cost?: string | null;
  shipping_cost?: string | null;
  cost?: string | null;
  tracking_number?: string | null;
  estimated_delivery?: string | null;
  status: string;
  checklist: Record<string, boolean> | null;
  issues?: string | null;
  notes?: string | null;
  approved: boolean;
  approved_at?: string | null;
  skipped: boolean;
  ordered_at: string;
}

export interface ProofCostEstimate {
  print_cost: string;
  shipping_cost: string;
  total: string;
  currency: string;
}

export interface ProofOrderCreateInput {
  interior_file_url: string;
  cover_file_url: string;
  trim_size?: string;
  page_count?: number;
  interior_type?: string;
  shipping_address: ShippingAddress;
  shipping_method: ShippingMethod;
}
