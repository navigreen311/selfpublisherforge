// Shared types across the application
export interface User {
  id: string;
  email: string;
  name: string;
  role: "owner" | "admin" | "editor" | "writer" | "viewer";
  org_id: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_tier: "free" | "starter" | "pro" | "business" | "enterprise";
}

export interface Project {
  id: string;
  title: string;
  type: "book" | "series" | "course";
  status: "draft" | "active" | "archived";
  created_at: string;
  updated_at: string;
}

export interface Book {
  id: string;
  project_id: string;
  title: string;
  subtitle?: string;
  isbn?: string;
  asin?: string;
  format: "ebook" | "print" | "audio";
  status: "draft" | "writing" | "editing" | "formatting" | "published";
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: string[];
    request_id: string;
  };
}
