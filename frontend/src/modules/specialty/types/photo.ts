export type PhotoUsageType = "style_reference" | "composition_reference" | "character_reference" | "background_reference" | "color_reference" | "texture_reference" | "pose_reference";
export interface PhotoReference { id: string; name: string; file_url: string; thumbnail_url?: string; usage_type: PhotoUsageType; description?: string; is_active: boolean; width?: number; height?: number; file_size_bytes?: number; mime_type?: string; created_at: string; updated_at: string; }
export interface PaginatedResponse<T> { items: T[]; total: number; page: number; page_size: number; }
