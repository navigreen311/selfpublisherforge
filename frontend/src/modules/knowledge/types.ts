/**
 * Type definitions for the Knowledge Base module.
 */

export interface KnowledgeEntry {
  id: string;
  org_id: string;
  title: string;
  content: string;
  source_url: string | null;
  source_type: "manual" | "url" | "file" | "clip";
  tags: string[];
  credibility_score: number | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface SearchHit {
  id: string;
  title: string;
  content_snippet: string;
  source_type: string;
  tags: string[];
  score: number;
  credibility_score: number | null;
  created_at: string | null;
}

export interface SearchResult {
  hits: SearchHit[];
  total: number;
  query: string;
}

export interface SummarizeResult {
  entry_id: string;
  summary: string;
  key_points: string[];
  suggested_tags: string[];
}

export interface TagList {
  tags: string[];
  counts: Record<string, number>;
}

export interface ImportPayload {
  url?: string;
  file_name?: string;
  file_content_base64?: string;
  extract_facts?: boolean;
}

export interface ImportResult {
  entry_id: string;
  title: string;
  content_preview: string;
  tags: string[];
  source_type: string;
  status: string;
}

export type KnowledgeCategory = "notes" | "research" | "characters" | "world-building" | "references" | "outlines" | "custom";

export interface KnowledgeAttachment {
  id: string;
  file_name: string;
  file_url: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

export interface Attachment {
  id: string;
  entry_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  url: string;
  created_at: string | null;
}

export interface CreateEntryPayload {
  title: string;
  content: string;
  category?: KnowledgeCategory;
  tags?: string[];
  source_type?: string;
  project_id?: string;
  source_url?: string;
}

export interface UpdateEntryPayload {
  title?: string;
  content?: string;
  category?: KnowledgeCategory;
  tags?: string[];
  project_id?: string;
}
