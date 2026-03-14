/**
 * TypeScript types for the Children's Book Studio.
 *
 * Covers book creation wizard, page spread editor, character consistency,
 * text readability, bilingual support, safety & provenance, and export.
 *
 * Blueprint refs: 3.1-3.9, 13.1, 14.1
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type AgeRange = "board" | "picture" | "early_reader" | "chapter";

export type IllustrationStyle =
  | "watercolor"
  | "cartoon"
  | "flat"
  | "storybook"
  | "realistic"
  | "crayon_pencil"
  | "collage"
  | "anime_manga";

export type ColorPalette =
  | "bright_vibrant"
  | "soft_pastel"
  | "warm_earthy"
  | "cool_dreamy"
  | "monochrome_accent";

export type StoryMode = "prose" | "rhyming" | "repetitive_cumulative";

export type CreationMode = "ai_generate" | "write_own" | "import_text";

export type BilingualLayout = "side_by_side" | "alternating" | "back_section";

export type FearIntensity = "none" | "mild" | "moderate";

export type Tone = "warm_reassuring" | "exciting" | "humorous" | "educational";

export type PageLayout =
  | "full_bleed"
  | "top_image_bottom_text"
  | "bottom_image_top_text"
  | "left_image_right_text"
  | "right_image_left_text"
  | "text_only"
  | "full_bleed_no_text";

export type TextPosition = "top" | "middle" | "bottom";

export type BookStatus = "draft" | "in_progress" | "published";

export type PageType = "story" | "title" | "dedication" | "credits" | "blank";

// ---------------------------------------------------------------------------
// Core interfaces
// ---------------------------------------------------------------------------

export interface ChildrensBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  age_range: AgeRange;
  page_count: number;
  trim_size: string;
  illustration_style: IllustrationStyle;
  color_palette: ColorPalette;
  story_mode: StoryMode;
  creation_mode: CreationMode;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: BilingualLayout;
  fear_intensity: FearIntensity;
  tone: Tone;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  status: BookStatus;
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ChildrensBookPage {
  id: string;
  book_id: string;
  page_number: number;
  page_type: PageType;
  layout: PageLayout;
  text_content?: string;
  translated_text?: string;
  text_font?: string;
  text_size?: number;
  text_color?: string;
  text_position?: TextPosition;
  text_plate_enabled: boolean;
  illustration_prompt?: string;
  illustration_url?: string;
  illustration_model?: string;
  illustration_seed?: string;
  contrast_score?: number;
  gutter_safe: boolean;
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
  setting_continuity_rules?: Record<string, unknown>;
  time_of_day_rules?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Wizard / creation payloads
// ---------------------------------------------------------------------------

export interface SafetySettings {
  no_weapons: boolean;
  no_scary_imagery: boolean;
  no_trademarks: boolean;
  no_stereotypes: boolean;
  age_appropriate_vocab: boolean;
  trademark_safe_prompts: boolean;
  content_sensitivity_precheck: boolean;
  provenance_logging: boolean;
}

export interface CreateChildrensBookRequest {
  title: string;
  subtitle?: string;
  author: string;
  age_range: AgeRange;
  page_count: number;
  trim_size: string;
  illustration_style: IllustrationStyle;
  color_palette: ColorPalette;
  story_mode: StoryMode;
  creation_mode: CreationMode;
  is_bilingual: boolean;
  bilingual_language?: string;
  bilingual_layout?: BilingualLayout;
  fear_intensity: FearIntensity;
  tone: Tone;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  story_prompt?: string;
  safety_settings: SafetySettings;
}

export interface UpdateChildrensBookRequest {
  title?: string;
  subtitle?: string;
  author?: string;
  age_range?: AgeRange;
  page_count?: number;
  trim_size?: string;
  illustration_style?: IllustrationStyle;
  color_palette?: ColorPalette;
  status?: BookStatus;
}

// ---------------------------------------------------------------------------
// Analysis results
// ---------------------------------------------------------------------------

export interface ReadabilityResult {
  age_range: AgeRange;
  max_sentence_length: number;
  max_word_length: number;
  vocabulary_level: string;
  total_words: number;
  flagged_words: { word: string; reason: string }[];
  flagged_sentences: { page: number; sentence: string; reason: string }[];
  read_aloud_rhythm_score: number;
  page_turn_surprise_map: { page: number; score: number }[];
  look_inside_score: number;
}

export interface RhymeAssistantResult {
  pattern: "AABB" | "ABAB" | "none";
  near_rhymes: { page: number; line: string; suggestion: string }[];
  meter_issues: { page: number; line: string; issue: string }[];
}

export interface ContinuityIssue {
  page_number: number;
  character_name: string;
  issue: string;
  fix_suggestion: string;
}

export interface ContinuityCheckResult {
  score: number;
  issues: ContinuityIssue[];
  style_drift_pages: number[];
}

export interface SafetyCheckResult {
  trademark_flags: { page: number; term: string }[];
  content_flags: { page: number; issue: string; severity: string }[];
  all_clear: boolean;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export interface ChildrensBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  pages_created: number;
}
