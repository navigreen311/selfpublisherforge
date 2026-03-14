export interface Comic { id: string; org_id: string; title: string; format: "single_issue" | "graphic_novel" | "manga" | "webcomic"; art_style: string; color_mode: string; ink_style: string; pacing: string; target_audience: string; page_count: number; trim_size: string; border_style: string; gutter_style: string; status: "draft" | "in-progress" | "published"; qa_score?: number; cover_image_url?: string; created_at: string; updated_at: string; }
export interface ComicStats { total_comics: number; in_progress: number; published: number; pages_created: number; panels_created: number; }
export interface CreateComicRequest { title: string; format: string; }
export interface UpdateComicRequest extends Partial<CreateComicRequest> { status?: string; }
