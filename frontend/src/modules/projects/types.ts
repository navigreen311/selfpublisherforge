export interface BookSummary {
  id: string;
  title: string;
  format: string;
  status: string;
}

export interface Project {
  id: string;
  title: string;
  description?: string | null;
  type: "book" | "series" | "course";
  status: "draft" | "active" | "archived" | "completed";
  settings: Record<string, unknown> | null;
  pen_name_id: string | null;
  genre?: string | null;
  subgenre?: string | null;
  target_audience?: string | null;
  keywords?: string[] | null;
  target_word_count?: number | null;
  target_date?: string | null;
  marketplace?: string | null;
  template?: string | null;
  cover_image_url?: string | null;
  language?: string | null;
  content_rating?: string | null;
  has_ai_content?: boolean;
  is_public_domain?: boolean;
  books: BookSummary[];
  created_at: string;
  updated_at: string;
}

export interface CreateProjectData {
  title: string;
  type: "book" | "series" | "course";
  genre?: string;
  subgenre?: string;
  pen_name?: string;
  description?: string;
  target_audience?: string;
  keywords?: string[];
  target_word_count?: number;
  target_date?: string;
  marketplace?: string;
  template?: string;
  cover_image_url?: string;
  language?: string;
  content_rating?: string;
  has_ai_content?: boolean;
  is_public_domain?: boolean;
}

export interface UpdateProjectData {
  title?: string;
  type?: "book" | "series" | "course";
  status?: "draft" | "active" | "archived" | "completed";
  settings?: Record<string, unknown>;
  genre?: string;
  subgenre?: string;
  description?: string;
  target_audience?: string;
  keywords?: string[];
  target_word_count?: number;
  target_date?: string;
  marketplace?: string;
  template?: string;
  cover_image_url?: string;
  language?: string;
  content_rating?: string;
  has_ai_content?: boolean;
  is_public_domain?: boolean;
}
