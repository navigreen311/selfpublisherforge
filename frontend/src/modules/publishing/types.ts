export interface PublishingAccount {
  id: string;
  org_id: string;
  platform: string;
  account_name: string;
  account_email: string | null;
  is_active: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAccountPayload {
  platform: string;
  account_name: string;
  account_email?: string;
  credentials?: Record<string, string>;
}

export interface ChapterInput {
  title: string;
  content: string;
  order: number;
}

export interface ExportRequest {
  book_id: string;
  format: "epub" | "pdf";
  chapters: ChapterInput[];
  template_id?: string | null;
  include_toc?: boolean;
  include_cover?: boolean;
  cover_image_url?: string | null;
  trim_size?: string;
  include_isbn_barcode?: boolean;
  isbn?: string | null;
}

export interface ExportResponse {
  id: string;
  book_id: string;
  format: "epub" | "pdf";
  status: string;
  file_url: string | null;
  file_size_bytes: number | null;
  page_count: number | null;
  created_at: string;
  message: string;
}

export interface StyleSettings {
  font_family: string;
  font_size_pt: number;
  line_height: number;
  margin_top_in: number;
  margin_bottom_in: number;
  margin_inner_in: number;
  margin_outer_in: number;
  chapter_heading_font: string;
  chapter_heading_size_pt: number;
  paragraph_indent_em: number;
  paragraph_spacing_pt: number;
  drop_cap: boolean;
  header_text: string | null;
  footer_text: string | null;
  page_numbers: boolean;
}

export interface FormattingTemplate {
  id: string;
  org_id: string | null;
  name: string;
  genre: string;
  description: string | null;
  trim_size: string;
  style_settings: StyleSettings;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface PricingInfo {
  currency: string;
  list_price: number;
  sale_price: number | null;
}

export interface BookMetadata {
  book_id: string;
  title: string;
  subtitle: string | null;
  description: string | null;
  authors: string[];
  keywords: string[];
  categories: string[];
  language: string;
  isbn: string | null;
  asin: string | null;
  publisher: string | null;
  publication_date: string | null;
  pricing: PricingInfo;
  series_name: string | null;
  series_number: number | null;
  page_count: number | null;
  age_range: string | null;
  updated_at: string;
}

export interface BookMetadataUpdate {
  title?: string;
  subtitle?: string;
  description?: string;
  authors?: string[];
  keywords?: string[];
  categories?: string[];
  language?: string;
  isbn?: string;
  asin?: string;
  publisher?: string;
  publication_date?: string;
  pricing?: Partial<PricingInfo>;
  series_name?: string;
  series_number?: number;
  page_count?: number;
  age_range?: string;
}

export interface ListingDetail {
  id: string;
  book_id: string;
  account_id: string;
  platform: string;
  platform_listing_id: string | null;
  status: string;
  listing_url: string | null;
  title: string | null;
  current_price: number | null;
  current_rank: number | null;
  reviews_count: number | null;
  rating: number | null;
  last_synced_at: string | null;
  sync_errors: string[];
  created_at: string;
  updated_at: string;
}

export type Severity = "error" | "warning" | "info";
export type ValidationType = "print" | "ebook" | "cover" | "compliance" | "full";
export type ValidationStatus = "passed" | "failed" | "warnings" | "pending";

export interface ValidationIssue {
  severity: Severity;
  rule: string;
  message: string;
  location?: string;
  details?: Record<string, any>;
}

export interface ValidationResult {
  validation_type: ValidationType;
  status: ValidationStatus;
  issues: ValidationIssue[];
  checked_at: string;
  metadata: Record<string, any>;
}

export interface FullValidationResponse {
  id: string;
  overall_status: ValidationStatus;
  results: ValidationResult[];
  total_errors: number;
  total_warnings: number;
  created_at: string;
}

export interface ISBN {
  id: string;
  isbn: string;
  format?: string;
  book_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateISBNPayload {
  isbn: string;
  format?: string;
  book_id?: string;
}

export interface BarcodeResponse {
  isbn_id: string;
  barcode_url: string;
  format: string;
}

export interface BookPricing {
  book_id: string;
  base_price: number;
  currency: string;
  royalty_rate: number;
  territories: Record<string, number>;
  updated_at: string;
}

export interface UpdatePricingPayload {
  base_price?: number;
  currency?: string;
  royalty_rate?: number;
  territories?: Record<string, number>;
}

export interface RoyaltyCalculation {
  list_price: number;
  royalty_rate: number;
  estimated_royalty: number;
  currency: string;
}

export interface CalculateRoyaltyPayload {
  book_id: string;
  list_price: number;
  territory?: string;
}

export interface ExportHistoryEntry {
  id: string;
  book_id: string;
  format: string;
  status: string;
  file_url: string | null;
  file_size_bytes: number | null;
  created_at: string;
}

export interface FullValidationRequest {
  print_validation?: {
    trim_size: string;
    page_count: number;
    paper_type?: string;
    has_bleed?: boolean;
    inside_margin: number;
    outside_margin: number;
    top_margin: number;
    bottom_margin: number;
    image_dpi?: number;
    fonts_embedded?: boolean;
    color_space?: string;
  };
  ebook_validation?: {
    has_ncx_toc?: boolean;
    has_html_toc?: boolean;
    images?: Array<{
      filename: string;
      format: string;
      size_bytes: number;
      dpi?: number;
    }>;
    links?: Array<{
      href: string;
      text?: string;
      is_internal?: boolean;
      is_valid?: boolean;
    }>;
    has_javascript?: boolean;
    has_external_resources?: boolean;
    min_font_size_pt?: number;
    file_size_bytes?: number;
  };
  cover_validation?: {
    cover_type?: string;
    width_inches: number;
    height_inches: number;
    dpi: number;
    file_format: string;
    color_space?: string;
    trim_size?: string;
    page_count?: number;
    paper_type?: string;
    has_text_in_bleed?: boolean;
  };
  compliance_scan?: {
    title?: string;
    subtitle?: string;
    description?: string;
    keywords?: string[];
    categories?: string[];
    content_sample?: string;
  };
}
