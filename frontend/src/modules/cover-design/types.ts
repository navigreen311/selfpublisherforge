// TypeScript types for cover design module

export type CoverGenre =
  | "romance"
  | "thriller"
  | "mystery"
  | "sci-fi"
  | "fantasy"
  | "horror"
  | "literary-fiction"
  | "nonfiction"
  | "self-help"
  | "business"
  | "childrens"
  | "young-adult"
  | "memoir"
  | "cookbook"
  | "other";

export type CoverStatus = "pending" | "generating" | "completed" | "failed";

export type CoverPlatform =
  | "amazon-kdp"
  | "ingram-spark"
  | "barnes-noble"
  | "apple-books"
  | "google-play"
  | "custom";

export interface CoverDimensions {
  width_px: number;
  height_px: number;
  dpi: number;
  bleed_px: number;
}

export interface Cover {
  id: string;
  org_id: string;
  book_id: string | null;
  title: string;
  subtitle: string | null;
  author_name: string;
  genre: CoverGenre;
  status: CoverStatus;
  image_url: string | null;
  thumbnail_url: string | null;
  prompt_used: string | null;
  dimensions: CoverDimensions | null;
  platform: CoverPlatform;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CoverTemplate {
  id: string;
  name: string;
  genre: CoverGenre;
  description: string;
  thumbnail_url: string | null;
  dimensions: CoverDimensions;
  font_recommendations: string[];
  layout_guidance: string | null;
  tags: string[];
}

export interface CoverGenerateRequest {
  book_id?: string;
  title: string;
  subtitle?: string;
  author_name: string;
  genre: CoverGenre;
  mood?: string;
  style_keywords?: string[];
  color_palette?: string[];
  platform?: CoverPlatform;
  additional_instructions?: string;
}

export interface CoverVariationRequest {
  variation_count: number;
  variation_type: "style" | "color" | "layout" | "typography";
  instructions?: string;
}

export interface ColorAnalysis {
  hex_code: string;
  percentage: number;
  name: string | null;
}

export interface CompetitorCoverAnalysis {
  image_url: string | null;
  dominant_colors: ColorAnalysis[];
  text_placement: string | null;
  imagery_style: string | null;
  overall_mood: string | null;
  font_style: string | null;
  effectiveness_score: number | null;
}

export interface CompetitorAnalysisResponse {
  genre: CoverGenre;
  niche_keywords: string[];
  analyses: CompetitorCoverAnalysis[];
  trends: Record<string, unknown>;
  recommendations: string[];
}

export interface CompetitorAnalysisRequest {
  genre: CoverGenre;
  niche_keywords: string[];
  competitor_image_urls?: string[];
  max_results?: number;
}
