export interface PlatformStats {
  total_users: number;
  active_users: number;
  total_organizations: number;
  active_organizations: number;
  mrr: number;
  active_subscriptions: number;
  total_api_calls_today: number;
  total_storage_gb: number;
}

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: "user" | "admin" | "superadmin";
  org_id: string;
  org_name: string;
  is_active: boolean;
  is_banned: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminOrganization {
  id: string;
  name: string;
  slug: string;
  plan_tier: "free" | "pro" | "enterprise";
  member_count: number;
  created_at: string;
  subscription_status: "active" | "cancelled" | "past_due" | null;
  mrr: number;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface UserFilters {
  search?: string;
  role?: string;
  is_active?: boolean;
  is_banned?: boolean;
}

export interface OrgFilters {
  search?: string;
  plan_tier?: string;
  subscription_status?: string;
}

export interface AuditLogFilters {
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PlatformStatsDetailed {
  users_total: number;
  users_active_week: number;
  organizations: number;
  books: number;
  ai_tasks_month: number;
  tokens_month: number;
  storage_used_bytes: number;
  monthly_revenue: number;
}

export interface ActivityLogEntry {
  id: string;
  user_name: string;
  user_email: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface AdminUserDetail {
  id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  org_id: string;
  org_name: string;
  last_active?: string;
  books_count: number;
  manuscripts_count: number;
  ai_tasks_count: number;
  permissions: string[];
}

export interface InviteUserPayload {
  email: string;
  role: string;
  message?: string;
}

export interface UpdateUserPayload {
  role?: string;
  status?: string;
  permissions?: string[];
}

export interface AdminOrgDetail {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  owner_name: string;
  member_count: number;
  books_count: number;
  storage_used_bytes: number;
  storage_limit_bytes: number;
  feature_toggles: Record<string, boolean>;
  created_at: string;
}

export interface UpdateOrgPayload {
  name?: string;
  feature_toggles?: Record<string, boolean>;
}

export interface BillingOverviewData {
  plan_name: string;
  plan_price: number;
  next_billing?: string;
  usage: {
    tokens: { used: number; limit: number };
    storage: { used: number; limit: number };
    users: { used: number; limit: number };
    books: { used: number; limit: number };
  };
  invoices: {
    id: string;
    date: string;
    description: string;
    amount: number;
    status: string;
    pdf_url?: string;
  }[];
}
