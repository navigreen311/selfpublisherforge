export type PipelineStatus = "draft" | "active" | "paused" | "completed" | "cancelled";
export type TaskType = "writing" | "editing" | "proofreading" | "formatting" | "review";
export type TaskStatus = "pending" | "in_progress" | "blocked" | "completed" | "cancelled";

export interface PipelineTask {
  id: string;
  pipeline_id: string;
  org_id: string;
  title: string;
  description?: string | null;
  type: TaskType;
  status: TaskStatus;
  assignee_id?: string | null;
  due_date?: string | null;
  depends_on: string[];
  completed_at?: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  id: string;
  org_id: string;
  book_id: string;
  name: string;
  description?: string | null;
  status: PipelineStatus;
  settings: Record<string, unknown>;
  deadline?: string | null;
  tasks: PipelineTask[];
  created_at: string;
  updated_at: string;
}

export interface PipelineSummary {
  id: string;
  org_id: string;
  book_id: string;
  name: string;
  status: PipelineStatus;
  deadline?: string | null;
  task_count: number;
  completed_task_count: number;
  overdue_task_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedPipelines {
  items: PipelineSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TimelineTask {
  id: string;
  title: string;
  type: TaskType;
  status: TaskStatus;
  assignee_id?: string | null;
  start_date?: string | null;
  due_date?: string | null;
  completed_at?: string | null;
  depends_on: string[];
  progress: number;
}

export interface TimelineView {
  pipeline_id: string;
  pipeline_name: string;
  deadline?: string | null;
  tasks: TimelineTask[];
  critical_path: string[];
}

export interface PipelineTemplate {
  id: string;
  org_id: string;
  name: string;
  description?: string | null;
  task_definitions: Record<string, unknown>[];
  settings?: Record<string, unknown> | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}
