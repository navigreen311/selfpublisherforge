/** Types for the Pen Name Management module. */

export interface PenName {
  id: string;
  org_id: string;
  user_id: string | null;
  display_name: string;
  amazon_author_url: string | null;
  bio: string | null;
  photo_url: string | null;
  genres: string[];
  is_default: boolean;
  book_count: number;
  created_at: string;
  updated_at: string;
}

export interface PenNameInput {
  display_name: string;
  amazon_author_url?: string | null;
  bio?: string | null;
  photo_url?: string | null;
  genres?: string[];
  is_default?: boolean;
}

export interface PenNameBook {
  id: string;
  title: string;
  type: string | null;
  status: string | null;
}

export interface PenNameAnalytics {
  revenue: number;
  sales: number;
  books_count: number;
  avg_rating: number | null;
  period: string;
}
