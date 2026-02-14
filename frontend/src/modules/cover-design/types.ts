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

export type CoverStatus = "pending" | "generating" | "completed" | "failed" | "draft" | "edited" | "exported" | "active";

export type CoverPlatform =
  | "amazon-kdp"
  | "ingram-spark"
  | "barnes-noble"
  | "apple-books"
  | "google-play"
  | "custom";

export type CoverFormat = "print" | "ebook" | "audiobook";

export type CoverArtStyle =
  | "photographic"
  | "illustrated"
  | "minimalist"
  | "typography-focused"
  | "abstract"
  | "vintage"
  | "modern"
  | "hand-drawn"
  | "3d-render";

export type CoverExportFormat = "jpg" | "png" | "pdf" | "psd" | "tiff";

export type ABTestStatus = "active" | "ended" | "draft";

export type GenerationJobStatus = "pending" | "processing" | "completed" | "failed";

export interface CoverDimensions {
  width_px: number;
  height_px: number;
  dpi: number;
  bleed_px: number;
}

export interface CoverEditorState {
  version: string;
  objects: unknown[];
  background?: string | Record<string, unknown>;
  [key: string]: unknown;
}

export interface CoverGenerationParams {
  description?: string;
  reference_images?: string[];
  art_style?: CoverArtStyle;
  trim_size?: string;
  page_count?: number;
  paper_type?: string;
  mood?: string;
  style_keywords?: string[];
  color_palette?: string[];
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
  format?: CoverFormat;
  editor_state?: CoverEditorState | null;
  generation_params?: CoverGenerationParams | null;
  parent_cover_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  version_label?: string;
  is_active?: boolean;
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
  art_style?: CoverArtStyle;
}

export interface CoverGenerateRequest {
  book_id?: string;
  title: string;
  subtitle?: string;
  author_name: string;
  genre: CoverGenre;
  description?: string;
  reference_images?: string[];
  format?: CoverFormat;
  variations?: number;
  art_style?: CoverArtStyle;
  trim_size?: string;
  page_count?: number;
  paper_type?: string;
  mood?: string;
  style_keywords?: string[];
  color_palette?: string[];
  platform?: CoverPlatform;
  additional_instructions?: string;
}

export interface CoverGenerationJobResponse {
  job_id: string;
  status: GenerationJobStatus;
  message?: string;
}

export interface CoverGenerationStatusResponse {
  job_id: string;
  status: GenerationJobStatus;
  progress?: number;
  covers?: Cover[];
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface CoverVariationRequest {
  variation_count: number;
  variation_type: "style" | "color" | "layout" | "typography";
  instructions?: string;
}

export interface CoverExportRequest {
  format: CoverExportFormat;
  include_bleed?: boolean;
  color_profile?: string;
  compression_quality?: number;
}

export interface CoverExportResponse {
  download_url: string;
  format: CoverExportFormat;
  file_size_bytes: number;
  expires_at: string;
}

export interface SaveEditorStateRequest {
  editor_state: CoverEditorState;
}

export interface CoverABTest {
  id: string;
  org_id: string;
  book_id: string | null;
  name: string;
  description?: string;
  cover_ids: string[];
  status: ABTestStatus;
  start_date?: string;
  end_date?: string;
  total_votes: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CoverABVote {
  id: string;
  ab_test_id: string;
  cover_id: string;
  voter_id?: string;
  voter_email?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface CreateABTestRequest {
  book_id?: string;
  name: string;
  description?: string;
  cover_ids: string[];
}

export interface CastVoteRequest {
  cover_id: string;
  voter_email?: string;
}

export interface ABTestResults {
  test: CoverABTest;
  votes_by_cover: Record<string, number>;
  covers: Cover[];
  winner?: Cover;
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

export interface DesignPatterns {
  common_layouts: string[];
  typography_trends: string[];
  color_schemes: string[];
  imagery_types: string[];
}

export interface CompetitorAnalysisResponse {
  genre: CoverGenre;
  niche_keywords: string[];
  analyses: CompetitorCoverAnalysis[];
  design_patterns?: DesignPatterns;
  trends: Record<string, unknown>;
  recommendations: string[];
}

export interface CompetitorAnalysisRequest {
  genre: CoverGenre;
  niche_keywords: string[];
  competitor_image_urls?: string[];
  max_results?: number;
  subcategory?: string;
}

export interface DuplicateCoverRequest {
  title?: string;
  author_name?: string;
}

export interface SetActiveCoverRequest {
  cover_id: string;
}
