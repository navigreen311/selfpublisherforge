"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const publishingKeys = {
  all: ["publishing"] as const,
  accounts: () => [...publishingKeys.all, "accounts"] as const,
  templates: () => [...publishingKeys.all, "templates"] as const,
  listings: () => [...publishingKeys.all, "listings"] as const,
  metadata: (bookId: string) => [...publishingKeys.all, "metadata", bookId] as const,
};

// ---------------------------------------------------------------------------
// Accounts
// ---------------------------------------------------------------------------

export function usePublishingAccounts() {
  return useQuery<PublishingAccount[]>({
    queryKey: publishingKeys.accounts(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/publishing/accounts");
      return data;
    },
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();
  return useMutation<PublishingAccount, Error, CreateAccountPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/publishing/accounts", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishingKeys.accounts() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (accountId) => {
      await api.delete(`/api/v1/publishing/accounts/${accountId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishingKeys.accounts() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export function useExportEpub() {
  return useMutation<ExportResponse, Error, ExportRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/publishing/export/epub", payload);
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useExportPdf() {
  return useMutation<ExportResponse, Error, ExportRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/publishing/export/pdf", payload);
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export function useFormattingTemplates() {
  return useQuery<FormattingTemplate[]>({
    queryKey: publishingKeys.templates(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/publishing/templates");
      return data;
    },
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation<FormattingTemplate, Error, Partial<FormattingTemplate>>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/publishing/templates", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishingKeys.templates() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export function useBookMetadata(bookId: string) {
  return useQuery<BookMetadata>({
    queryKey: publishingKeys.metadata(bookId),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/books/${bookId}/metadata`);
      return data;
    },
    enabled: !!bookId,
  });
}

export function useUpdateMetadata(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<BookMetadata, Error, BookMetadataUpdate>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`/api/v1/books/${bookId}/metadata`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishingKeys.metadata(bookId) });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Listings
// ---------------------------------------------------------------------------

export function useListings() {
  return useQuery<ListingDetail[]>({
    queryKey: publishingKeys.listings(),
    queryFn: async () => {
      const { data } = await api.get("/api/v1/publishing/listings");
      return data;
    },
  });
}

export function useSyncListing() {
  const queryClient = useQueryClient();
  return useMutation<{ listing_id: string; status: string; message: string }, Error, string>({
    mutationFn: async (listingId) => {
      const { data } = await api.post(`/api/v1/publishing/listings/${listingId}/sync`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishingKeys.listings() });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
