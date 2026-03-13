// Children's Book module types

export type AgeRange = "board" | "picture" | "early_reader" | "chapter";
export type BookStatus = "draft" | "generating" | "illustrating" | "reviewing" | "published" | "archived";
export type IllustrationStyle = "watercolor" | "cartoon" | "flat" | "storybook" | "realistic" | "crayon_pencil" | "collage" | "anime_manga";
export type ColorPalette = "bright_vibrant" | "soft_pastel" | "warm_earthy" | "cool_dreamy" | "monochrome_accent";
export type PageLayout = "full_bleed" | "top_image_bottom_text" | "bottom_image_top_text" | "left_image_right_text" | "right_image_left_text" | "text_only" | "full_bleed_no_text";
export type TrimSize = "8.5x8.5" | "8.5x11" | "10x8" | "6x9";
export type CreationMode = "ai_generate" | "write_own" | "import_text";
export type StoryMode = "prose" | "rhyming_aabb" | "rhyming_abab" | "repetitive_cumulative";
export type Tone = "warm_reassuring" | "exciting" | "humorous" | "educational";
export type FearLevel = "none" | "mild" | "moderate";
export type BilingualLayout = "side_by_side" | "alternating" | "back_section";
export type PreviewDevice = "phone" | "desktop";

export interface Character {
  id: string;
  book_id: string;
  name: string;
  species_type: string;
  description: string;
  reference_images: { front?: string; side?: string; happy?: string; scared?: string };
  clothing_rules: string;
  scale_rules: string;
  setting_continuity: string;
  time_of_day_rules: string;
  created_at: string;
}

export interface PageText {
  content: string;
  font: string;
  size: number;
  color: string;
  position: "top" | "middle" | "bottom";
}

export interface PageIllustration {
  prompt: string;
  image_url?: string;
  character_consistency: boolean;
  trademark_safe: boolean;
  provenance?: { model: string; seed: number; date: string };
}

export interface BookPage {
  id: string;
  book_id: string;
  page_number: number;
  layout: PageLayout;
  text: PageText;
  illustration: PageIllustration;
  created_at: string;
  updated_at: string;
}

export interface SafetySettings {
  fear_intensity: FearLevel;
  no_weapons: boolean;
  no_scary_imagery: boolean;
  no_trademarked_characters: boolean;
  no_stereotypes: boolean;
  age_appropriate_vocabulary: boolean;
  trademark_safe_prompts: boolean;
  content_sensitivity_check: boolean;
  provenance_logging: boolean;
}

export interface TextAnalysisResult {
  readability_score: number;
  read_aloud_rhythm: number;
  avg_sentence_length: number;
  max_word_length: number;
  vocabulary_level: string;
  total_words: number;
  issues: { page: number; issue: string; suggestion: string }[];
}

export interface PreflightResult {
  passed: boolean;
  checks: { name: string; status: "pass" | "warn" | "fail"; message: string }[];
}

export interface ChildrensBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author: string;
  age_range: AgeRange;
  status: BookStatus;
  page_count: number;
  trim_size: TrimSize;
  illustration_style: IllustrationStyle;
  color_palette: ColorPalette;
  creation_mode: CreationMode;
  story_mode: StoryMode;
  tone: Tone;
  safety_settings: SafetySettings;
  bilingual: boolean;
  secondary_language?: string;
  bilingual_layout?: BilingualLayout;
  story_prompt?: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
  qa_score?: number;
  cover_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateChildrensBookPayload {
  title: string;
  subtitle?: string;
  author: string;
  age_range: AgeRange;
  page_count: number;
  trim_size: TrimSize;
  illustration_style: IllustrationStyle;
  color_palette: ColorPalette;
  creation_mode: CreationMode;
  story_mode: StoryMode;
  tone: Tone;
  safety_settings: SafetySettings;
  bilingual: boolean;
  secondary_language?: string;
  bilingual_layout?: BilingualLayout;
  story_prompt?: string;
  theme_moral?: string;
  main_character?: string;
  setting?: string;
}

export interface ChildrensBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  pages_created: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
