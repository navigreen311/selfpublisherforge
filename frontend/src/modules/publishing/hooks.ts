"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import type {
  PublishingAccount,
  CreateAccountPayload,
  ChapterInput,
  ExportRequest,
  ExportResponse,
  StyleSettings,
  FormattingTemplate,
  PricingInfo,
  BookMetadata,
  BookMetadataUpdate,
  ListingDetail,
  Severity,
  ValidationType,
  ValidationStatus,
  ValidationIssue,
  ValidationResult,
  FullValidationResponse,
  FullValidationRequest,
} from "./types";

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const publishingKeys = {
  all: ["publishing"] as const,
  accounts: () => [...publishingKeys.all, "accounts"] as const,
  templates: () => [...publishingKeys.all, "templates"] as const,
  listings: () => [...publishingKeys.all, "listings"] as const,
  metadata: (bookId: string) => [...publishingKeys.all, "metadata", bookId] as const,
  validation: (validationId: string) => [...publishingKeys.all, "validation", validationId] as const,
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

// ---------------------------------------------------------------------------
// KDP Validation
// ---------------------------------------------------------------------------

export function useRunFullValidation() {
  return useMutation<FullValidationResponse, Error, FullValidationRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post("/api/v1/publishing/validate", payload);
      return data;
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useValidationResults(validationId: string) {
  return useQuery<FullValidationResponse>({
    queryKey: publishingKeys.validation(validationId),
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/publishing/validate/${validationId}/results`);
      return data;
    },
    enabled: !!validationId,
  });
}
