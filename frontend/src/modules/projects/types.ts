export interface BookSummary {
  id: string;
  title: string;
  format: string;
  status: string;
}

export interface Project {
  id: string;
  title: string;
  type: "book" | "series" | "course";
  status: "draft" | "active" | "archived" | "completed";
  settings: Record<string, unknown> | null;
  pen_name_id: string | null;
  books: BookSummary[];
  created_at: string;
  updated_at: string;
}

export interface CreateProjectData {
  title: string;
  type: "book" | "series" | "course";
  genre?: string;
  pen_name?: string;
  description?: string;
}

export interface UpdateProjectData {
  title?: string;
  type?: "book" | "series" | "course";
  status?: "draft" | "active" | "archived" | "completed";
  settings?: Record<string, unknown>;
}
