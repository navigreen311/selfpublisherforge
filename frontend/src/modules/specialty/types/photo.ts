/**
 * TypeScript types for Photo Integration.
 */

export type PhotoUsageType =
  | "style_reference"
  | "composition_reference"
  | "character_reference"
  | "background_reference"
  | "color_reference"
  | "texture_reference"
  | "pose_reference";

export interface PhotoReference {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  file_url: string;
  thumbnail_url?: string;
  file_size_bytes?: number;
  mime_type?: string;
  width?: number;
  height?: number;
  usage_type: PhotoUsageType;
  tags?: string[];
  metadata_json?: Record<string, unknown>;
  book_type?: string;
  book_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UploadPhotoRequest {
  name: string;
  description?: string;
  usage_type: PhotoUsageType;
  book_type?: string;
  book_id?: string;
}

export interface GenerateWithRefsRequest {
  reference_ids: string[];
  prompt: string;
  usage_types?: PhotoUsageType[];
}

export interface GenerateWithRefsResponse {
  image_url: string;
  model: string;
  seed: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
