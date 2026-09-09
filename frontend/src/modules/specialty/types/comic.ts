export interface Comic {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  author?: string;
  artist?: string;
  format: "single_issue" | "graphic_novel" | "manga" | "webcomic" | "kids_comic" | "mini_series" | "one_shot" | "trade_paperback";
  art_style: string;
  color_mode: string;
  ink_style: string;
  pacing: string;
  target_audience: string;
  page_count: number;
  trim_size: string;
  border_style: string;
  gutter_style: string;
  genre?: string;
  premise?: string;
  content_rating?: string;
  violence_level?: string;
  language_level?: string;
  safety_settings?: Record<string, boolean>;
  status: "draft" | "in-progress" | "published";
  qa_score?: number;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ComicPage {
  id: string;
  comic_id: string;
  page_number: number;
  page_type?: string;
  layout_template?: string;
  panel_count: number;
  panels?: ComicPanel[];
  script_text?: string;
  artwork_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ComicPanel {
  id: string;
  page_id: string;
  panel_number: number;
  panel_type?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  border_style?: string;
  background_color?: string;
  description?: string;
  art_prompt?: string;
  art_url?: string;
  art_model?: string;
  script_text?: string;
  artwork_url?: string;
  bubbles?: ComicBubble[];
  created_at: string;
  updated_at: string;
}

export interface ComicBubble {
  id: string;
  panel_id: string;
  type: "speech" | "thought" | "narration" | "sfx" | "whisper" | "shout";
  bubble_type?: string;
  character_name?: string;
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  font?: string;
  font_size?: number;
  tail_direction?: string;
  font_style?: string;
}

export interface ComicCharacter {
  id: string;
  comic_id: string;
  name: string;
  role?: string;
  description?: string;
  visual_description?: string;
  reference_images: string[];
  auto_append: boolean;
  default_costume?: string;
  color_palette?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ComicStats {
  total_comics: number;
  in_progress: number;
  published: number;
  pages_created: number;
  panels_created: number;
}

export interface CreateComicRequest {
  title: string;
  format: string;
  art_style?: string;
  color_mode?: string;
  ink_style?: string;
  pacing?: string;
  target_audience?: string;
  page_count?: number;
  trim_size?: string;
  border_style?: string;
  gutter_style?: string;
}

export interface UpdateComicRequest extends Partial<CreateComicRequest> {
  status?: string;
}

export interface LayoutTemplate {
  id: string;
  name: string;
  panel_count: number;
  thumbnail_url?: string;
  description?: string;
}

