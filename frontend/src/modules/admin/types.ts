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
