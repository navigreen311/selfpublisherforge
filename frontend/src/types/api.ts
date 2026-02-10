/**
 * TypeScript types mirroring backend Pydantic schemas.
 *
 * These are the canonical API-layer types used by hooks, services, and
 * components.  Keep in sync with:
 *   - backend/app/schemas/common.py
 *   - backend/app/schemas/requests.py
 *   - backend/app/schemas/responses.py
 *   - shared/types/enums.py
 */

// ---------------------------------------------------------------------------
// Enums (mirrors shared/types/enums.py)
// ---------------------------------------------------------------------------

export enum PlanTier {
  FREE = "free",
  STARTER = "starter",
  PRO = "pro",
  BUSINESS = "business",
  ENTERPRISE = "enterprise",
}

export enum UserRole {
  OWNER = "owner",
  ADMIN = "admin",
  EDITOR = "editor",
  WRITER = "writer",
  VIEWER = "viewer",
}

export enum StatusEnum {
  DRAFT = "draft",
  ACTIVE = "active",
  ARCHIVED = "archived",
  DELETED = "deleted",
}

export enum BookFormat {
  EBOOK = "ebook",
  PRINT = "print",
  AUDIO = "audio",
}

export enum BookStatus {
  DRAFT = "draft",
  WRITING = "writing",
  EDITING = "editing",
  FORMATTING = "formatting",
  PUBLISHED = "published",
}

export enum ProjectType {
  BOOK = "book",
  SERIES = "series",
  COURSE = "course",
}

export enum CampaignStatus {
  DRAFT = "draft",
  SCHEDULED = "scheduled",
  ACTIVE = "active",
  PAUSED = "paused",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

export enum AgentType {
  WRITING = "writing",
  EDITING = "editing",
  RESEARCH = "research",
  MARKETING = "marketing",
  COVER_DESIGN = "cover_design",
  FORMATTING = "formatting",
  ANALYTICS = "analytics",
}

export enum SortDirection {
  ASC = "asc",
  DESC = "desc",
}

export enum FilterOperator {
  EQ = "eq",
  NEQ = "neq",
  GT = "gt",
  GTE = "gte",
  LT = "lt",
  LTE = "lte",
  IN = "in",
  CONTAINS = "contains",
  STARTS_WITH = "starts_with",
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  field: string | null;
  message: string;
  code: string | null;
}

export interface ErrorResponse {
  code: string;
  message: string;
  details: ErrorDetail[];
  request_id: string;
}

export interface ApiError {
  error: ErrorResponse;
}

// ---------------------------------------------------------------------------
// Success / response envelopes
// ---------------------------------------------------------------------------

export interface SuccessResponse<T> {
  data: T;
  meta?: Record<string, unknown> | null;
}

export interface PaginatedMeta {
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface PaginatedSuccessResponse<T> {
  data: T[];
  meta: PaginatedMeta;
}

// ---------------------------------------------------------------------------
// Common request types
// ---------------------------------------------------------------------------

export interface SortParams {
  sort_by?: string;
  sort_dir?: SortDirection;
}

export interface FilterParams {
  field: string;
  operator: FilterOperator;
  value: string | number | boolean | string[];
}

export interface DateRangeFilter {
  field?: string;
  start?: string | null;
  end?: string | null;
}

export interface CursorParams {
  cursor?: string | null;
  limit?: number;
}

export interface BulkActionRequest {
  ids: string[];
  action: string;
  params?: Record<string, string | number | boolean> | null;
}

// ---------------------------------------------------------------------------
// Bulk action response
// ---------------------------------------------------------------------------

export interface BulkItemResult {
  id: string;
  success: boolean;
  error: string | null;
}

export interface BulkActionResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: BulkItemResult[];
}

// ---------------------------------------------------------------------------
// Common model mixins
// ---------------------------------------------------------------------------

export interface TimestampMixin {
  created_at: string;
  updated_at: string;
}

export interface OrgScoped {
  org_id: string;
}

// ---------------------------------------------------------------------------
// Health / Message
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
}

export interface MessageResponse {
  message: string;
}
