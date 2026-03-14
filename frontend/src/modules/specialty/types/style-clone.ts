/**
 * TypeScript types for Art Style Cloning.
 */

export interface StyleCloneProfile {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  reference_image_urls?: string[];
  reference_count: number;
  style_attributes?: StyleAttributes;
  style_prompt?: string;
  test_image_urls?: string[];
  drift_score?: number;
  last_drift_check?: string;
  book_type?: string;
  is_active: boolean;
  is_default: boolean;
  times_used: number;
  created_at: string;
  updated_at: string;
}

export interface StyleAttributes {
  line_weight?: string;
  color_saturation?: string;
  shading_technique?: string;
  perspective?: string;
  palette_dominant?: string[];
  texture?: string;
  composition_style?: string;
}

export interface CreateStyleCloneRequest {
  name: string;
  description?: string;
  reference_image_urls: string[];
  book_type?: string;
}

export interface UpdateStyleCloneRequest {
  name?: string;
  description?: string;
  reference_image_urls?: string[];
  is_active?: boolean;
}

export interface StyleAnalysisResult {
  profile_id: string;
  style_attributes: StyleAttributes;
  style_prompt: string;
  confidence: number;
}

export interface TestGenerateResult {
  profile_id: string;
  test_images: string[];
}

export interface DriftCheckResult {
  profile_id: string;
  drift_score: number;
  drift_level: "low" | "medium" | "high";
  details: {
    color_drift: number;
    line_weight_drift: number;
    composition_drift: number;
  };
  recommendation: string;
}

export interface PaginatedStyleCloneResponse {
  items: StyleCloneProfile[];
  total: number;
  page: number;
  page_size: number;
}
