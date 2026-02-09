/**
 * TypeScript types for the AI Agent System.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type AgentType =
  | "research"
  | "writing_assistant"
  | "editor"
  | "marketing_copy";

export type PermissionLevel =
  | "draft_only"
  | "suggest"
  | "auto_execute_low"
  | "auto_execute_high"
  | "full_autonomous";

export type TaskStatus =
  | "pending"
  | "running"
  | "awaiting_approval"
  | "approved"
  | "rejected"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskPriority = "low" | "medium" | "high" | "critical";

export type WorkflowStatus =
  | "draft"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type AuditAction =
  | "task_created"
  | "task_started"
  | "task_completed"
  | "task_failed"
  | "task_approved"
  | "task_rejected"
  | "task_cancelled"
  | "workflow_created"
  | "workflow_started"
  | "workflow_completed"
  | "workflow_failed"
  | "config_updated"
  | "budget_updated"
  | "budget_alert"
  | "emergency_stop"
  | "permission_changed";

// ---------------------------------------------------------------------------
// Agent
// ---------------------------------------------------------------------------

export interface Agent {
  id: string;
  org_id: string;
  agent_type: AgentType;
  name: string;
  description: string | null;
  is_enabled: boolean;
  permission_level: PermissionLevel;
  model_id: string;
  system_prompt: string | null;
  max_tokens: number;
  temperature: number;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AgentConfigUpdate {
  name?: string;
  description?: string;
  is_enabled?: boolean;
  permission_level?: PermissionLevel;
  model_id?: string;
  system_prompt?: string;
  max_tokens?: number;
  temperature?: number;
  config?: Record<string, unknown>;
}

export interface AgentListResponse {
  items: Agent[];
  total_count: number;
}

// ---------------------------------------------------------------------------
// Task
// ---------------------------------------------------------------------------

export interface TaskCreate {
  agent_id: string;
  title: string;
  description?: string;
  priority?: TaskPriority;
  input_data?: Record<string, unknown>;
}

export interface AgentTask {
  id: string;
  org_id: string;
  agent_id: string;
  workflow_id: string | null;
  workflow_step_index: number | null;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  tokens_used: number;
  cost_usd: number;
  quality_score: number | null;
  created_by: string;
  approved_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: AgentTask[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

// ---------------------------------------------------------------------------
// Workflow
// ---------------------------------------------------------------------------

export interface WorkflowStepDefinition {
  agent_id: string;
  title: string;
  description?: string;
  input_data?: Record<string, unknown>;
  condition?: string;
  on_failure?: "stop" | "skip" | "retry";
  max_retries?: number;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  steps: WorkflowStepDefinition[];
}

export interface AgentWorkflow {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  status: WorkflowStatus;
  steps: Record<string, unknown>[];
  current_step_index: number;
  context: Record<string, unknown> | null;
  error_message: string | null;
  created_by: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  items: AgentWorkflow[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

// ---------------------------------------------------------------------------
// Budget
// ---------------------------------------------------------------------------

export interface BudgetStatus {
  id: string;
  org_id: string;
  agent_id: string;
  daily_token_limit: number;
  daily_usd_limit: number;
  monthly_usd_limit: number;
  tokens_used_today: number;
  usd_used_today: number;
  usd_used_this_month: number;
  total_tokens_used: number;
  total_usd_used: number;
  last_reset_daily: string | null;
  last_reset_monthly: string | null;
  daily_token_pct: number;
  daily_usd_pct: number;
  monthly_usd_pct: number;
}

export interface BudgetUpdate {
  daily_token_limit?: number;
  daily_usd_limit?: number;
  monthly_usd_limit?: number;
}

export interface BudgetListResponse {
  items: BudgetStatus[];
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export interface AuditEntry {
  id: string;
  org_id: string;
  action: AuditAction;
  actor_id: string;
  actor_type: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditListResponse {
  items: AuditEntry[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

// ---------------------------------------------------------------------------
// Emergency Stop
// ---------------------------------------------------------------------------

export interface EmergencyStopResponse {
  tasks_cancelled: number;
  workflows_cancelled: number;
  message: string;
}
