// Shared types across the application
//
// Re-export canonical types from api.ts and modules.ts so that imports
// from "@/types" always resolve to the single source of truth.
//
// api.ts   -- enums, error shapes, request/response envelopes
// modules.ts -- domain model interfaces (User, Book, Campaign, etc.)

export type {
  ApiError,
  PaginatedResponse,
  PaginatedSuccessResponse,
  SuccessResponse,
  PaginatedMeta,
} from "./api";

// Re-export all module domain types for convenience
export * from "./modules";
