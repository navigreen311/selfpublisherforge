export interface PenName {
  id: string;
  display_name: string;
  amazon_url: string | null;
  bio: string | null;
  photo_url: string | null;
  genres: string[];
  is_default: boolean;
  book_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PenNameCreatePayload {
  display_name: string;
  amazon_url?: string | null;
  bio?: string | null;
  photo_url?: string | null;
  genres?: string[];
  is_default?: boolean;
}

export type PenNameUpdatePayload = Partial<PenNameCreatePayload>;

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
  avg_rating: number;
  period: string;
}

export const PEN_NAME_GENRES: { value: string; label: string }[] = [
  { value: "childrens", label: "Children's Books" },
  { value: "coloring", label: "Coloring Books" },
  { value: "puzzle", label: "Puzzle Books" },
  { value: "comic", label: "Comic Books" },
  { value: "cookbook", label: "Cookbooks" },
  { value: "nonfiction", label: "Nonfiction" },
  { value: "fiction", label: "Fiction" },
];
