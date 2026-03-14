"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChildrensBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  age_range: "board" | "picture" | "early_reader" | "chapter";
  page_count: number;
  trim_size: string;
  illustration_style: string;
  color_palette: string;
  style_clone_id?: string;
  story_mode: string;
  creation_mode: string;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: string;
  fear_intensity: string;
  tone: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  status: "draft" | "in-progress" | "published";
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ChildrensBookPage {
  id: string;
  book_id: string;
  page_number: number;
  page_type: string;
  layout: string;
  text_content?: string;
  translated_text?: string;
  text_font?: string;
  text_size?: number;
  text_color?: string;
  text_position?: string;
  illustration_prompt?: string;
  illustration_url?: string;
  illustration_model?: string;
  text_plate_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChildrensBookCharacter {
  id: string;
  book_id: string;
  name: string;
  species?: string;
  description: string;
  reference_images: string[];
  auto_append: boolean;
  clothing_rules?: Record<string, unknown>;
  scale_rules?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateChildrensBookPayload {
  title: string;
  subtitle?: string;
  author: string;
  age_range: string;
  page_count: number;
  trim_size: string;
  illustration_style: string;
  color_palette: string;
  story_mode: string;
  creation_mode: string;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: string;
  fear_intensity: string;
  tone: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  safety_settings: Record<string, boolean>;
}

export interface UpdateChildrensBookPayload {
  title?: string;
  subtitle?: string;
  author?: string;
  age_range?: string;
  page_count?: number;
  trim_size?: string;
  illustration_style?: string;
  color_palette?: string;
  status?: string;
}

export interface ChildrensBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  pages_created: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Continuity QA Types
// ---------------------------------------------------------------------------

export type ContinuityIssueType =
  | "missing_clothing"
  | "scale_mismatch"
  | "location_inconsistency"
  | "time_of_day_mismatch"
  | "style_drift";

export type ContinuitySeverity = "critical" | "warning" | "info";

export interface ContinuityIssue {
  id: string;
  page: number;
  issueType: ContinuityIssueType;
  description: string;
  severity: ContinuitySeverity;
  autoFixable: boolean;
}

export interface AutoFixResult {
  fixed_count: number;
  remaining_issues: ContinuityIssue[];
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/childrens-books";

export const childrensBookKeys = {
  all: ["childrens-books"] as const,
  list: (params?: Record<string, unknown>) =>
    [...childrensBookKeys.all, "list", params] as const,
  detail: (id: string) => [...childrensBookKeys.all, "detail", id] as const,
  pages: (bookId: string) =>
    [...childrensBookKeys.all, "pages", bookId] as const,
  characters: (bookId: string) =>
    [...childrensBookKeys.all, "characters", bookId] as const,
  continuity: (bookId: string) =>
    [...childrensBookKeys.all, "continuity", bookId] as const,
  stats: () => [...childrensBookKeys.all, "stats"] as const,
};

// ---------------------------------------------------------------------------
// List / Stats
// ---------------------------------------------------------------------------

export function useChildrensBooks(
  page = 1,
  pageSize = 20,
  filters?: { status?: string; age_range?: string; search?: string },
) {
  return useQuery<PaginatedResponse<ChildrensBook>>({
    queryKey: childrensBookKeys.list({ page, pageSize, ...filters }),
    queryFn: async () => {
      const { data } = await api.get(API_BASE, {
        params: {
          page,
          page_size: pageSize,
          ...filters,
        },
      });
      return data;
    },
  });
}

export function useChildrensBookStats() {
  return useQuery<ChildrensBookStats>({
    queryKey: childrensBookKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/stats`);
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Single Book CRUD
// ---------------------------------------------------------------------------

export function useChildrensBook(id: string) {
  return useQuery<ChildrensBook>({
    queryKey: childrensBookKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateChildrensBook() {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBook, Error, CreateChildrensBookPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(API_BASE, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
      toast.success("Children's book created successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateChildrensBook(id: string) {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBook, Error, UpdateChildrensBookPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`${API_BASE}/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.detail(id),
      });
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteChildrensBook() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (bookId) => {
      await api.delete(`${API_BASE}/${bookId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: childrensBookKeys.all });
      toast.success("Book deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

export function useBookPages(bookId: string) {
  return useQuery<ChildrensBookPage[]>({
    queryKey: childrensBookKeys.pages(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${bookId}/pages`);
      return data;
    },
    enabled: !!bookId,
  });
}

// ---------------------------------------------------------------------------
// Illustration Actions
// ---------------------------------------------------------------------------

export interface GenerateIllustrationPayload {
  prompt: string;
}

export interface GenerateIllustrationResponse {
  illustration_url: string;
}

export interface UploadImageResponse {
  illustration_url: string;
}

export interface GenerateVariationsResponse {
  variation_urls: string[];
}

export function useGenerateIllustration(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    GenerateIllustrationResponse,
    Error,
    { pageId: string; prompt: string }
  >({
    mutationFn: async ({ pageId, prompt }) => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/pages/${pageId}/generate-illustration`,
        { prompt },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
      toast.success("Illustration generated successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUploadImage(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<UploadImageResponse, Error, { pageId: string; file: File }>(
    {
      mutationFn: async ({ pageId, file }) => {
        const formData = new FormData();
        formData.append("file", file);
        const { data } = await api.post(
          `${API_BASE}/${bookId}/pages/${pageId}/upload-image`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } },
        );
        return data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: childrensBookKeys.pages(bookId),
        });
        toast.success("Image uploaded successfully");
      },
      onError: (error) => {
        toast.error(extractApiError(error));
      },
    },
  );
}

export function useGenerateVariations(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    GenerateVariationsResponse,
    Error,
    { pageId: string }
  >({
    mutationFn: async ({ pageId }) => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/pages/${pageId}/generate-variations`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
      toast.success("Variations generated successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Characters
// ---------------------------------------------------------------------------

export function useBookCharacters(bookId: string) {
  return useQuery<ChildrensBookCharacter[]>({
    queryKey: childrensBookKeys.characters(bookId),
    queryFn: async () => {
      const { data } = await api.get(`${API_BASE}/${bookId}/characters`);
      return data;
    },
    enabled: !!bookId,
  });
}

export interface CreateCharacterPayload {
  name: string;
  species?: string;
  description: string;
  auto_append: boolean;
  clothing_rules?: Record<string, unknown>;
  scale_rules?: Record<string, unknown>;
}

export interface UpdateCharacterPayload
  extends Partial<CreateCharacterPayload> {}

export function useCreateCharacter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<ChildrensBookCharacter, Error, CreateCharacterPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/characters`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
      toast.success("Character created");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useUpdateCharacter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ChildrensBookCharacter,
    Error,
    { characterId: string; payload: UpdateCharacterPayload }
  >({
    mutationFn: async ({ characterId, payload }) => {
      const { data } = await api.patch(
        `${API_BASE}/${bookId}/characters/${characterId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
      toast.success("Character updated");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useDeleteCharacter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (characterId) => {
      await api.delete(`${API_BASE}/${bookId}/characters/${characterId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
      toast.success("Character deleted");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export interface GenerateReferencesResponse {
  reference_images: string[];
}

export function useGenerateReferences(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    GenerateReferencesResponse,
    Error,
    { characterId: string; view: string }
  >({
    mutationFn: async ({ characterId, view }) => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/characters/${characterId}/generate-references`,
        { view },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.characters(bookId),
      });
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Continuity QA
// ---------------------------------------------------------------------------

export function useContinuityCheck(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<ContinuityIssue[], Error>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/continuity-check`,
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(childrensBookKeys.continuity(bookId), data);
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

export function useAutoFixPrompts(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<AutoFixResult, Error>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/auto-fix-prompts`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.continuity(bookId),
      });
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.pages(bookId),
      });
      toast.success("Auto-fix applied successfully");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Safety Check
// ---------------------------------------------------------------------------

export interface TrademarkHit {
  id: string;
  page: number;
  term: string;
  context: string;
}

export type Severity = "critical" | "warning" | "info";

export type SensitivityCategory =
  | "violence"
  | "fear"
  | "stereotypes"
  | "mature_themes";

export interface SensitivityIssue {
  id: string;
  page: number;
  category: SensitivityCategory;
  description: string;
  severity: Severity;
}

export interface SafetyCheckResponse {
  trademark_hits: TrademarkHit[];
  sensitivity_issues: SensitivityIssue[];
}

export function useSafetyCheck(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation<SafetyCheckResponse, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_BASE}/${bookId}/safety-check`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: childrensBookKeys.detail(bookId),
      });
      toast.success("Safety scan complete");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

// ---------------------------------------------------------------------------
// Provenance
// ---------------------------------------------------------------------------

export interface PageProvenance {
  page: number;
  model: string;
  promptHash: string;
  seed: string;
  generatedDate: string;
  status: "verified" | "pending" | "missing";
}

export interface FontLicenseEntry {
  fontName: string;
  licenseType: string;
  commercialPrintSafe: boolean;
}

export interface ProvenanceResponse {
  pages: PageProvenance[];
  fonts: FontLicenseEntry[];
}

const PROVENANCE_API_BASE = "/api/v1/specialty";

export const provenanceKeys = {
  detail: (bookType: string, bookId: string) =>
    ["provenance", bookType, bookId] as const,
};

export function useProvenance(bookType: string, bookId: string) {
  return useQuery<ProvenanceResponse>({
    queryKey: provenanceKeys.detail(bookType, bookId),
    queryFn: async () => {
      const { data } = await api.get(
        `${PROVENANCE_API_BASE}/${bookType}/${bookId}/provenance`,
      );
      return data;
    },
    enabled: !!bookType && !!bookId,
  });
}

export function useExportProvenance(bookType: string, bookId: string) {
  return useMutation<Blob, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${PROVENANCE_API_BASE}/${bookType}/${bookId}/provenance/export`,
        {},
        { responseType: "blob" },
      );
      return data;
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `provenance-report-${bookId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Compliance report exported");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}
