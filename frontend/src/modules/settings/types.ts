// Organization Settings
export interface OrgSettings {
  name: string;
  website?: string;
  industry?: string;
  imprint_name?: string;
  publisher_id?: string;
  default_genre?: string;
  default_marketplace?: string;
  default_currency: string;
  team_members: TeamMember[];
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface OrgSettingsUpdate {
  name?: string;
  website?: string;
  industry?: string;
  imprint_name?: string;
  default_genre?: string;
  default_marketplace?: string;
  default_currency?: string;
}

// Security
export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export interface SessionInfo {
  id: string;
  device: string;
  browser: string;
  os: string;
  ip_address: string;
  location: string;
  is_current: boolean;
  last_active_at: string;
}

export interface LoginHistoryEntry {
  id: string;
  device: string;
  browser: string;
  ip_address: string;
  location: string;
  success: boolean;
  created_at: string;
}

// API Keys
export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  last_used_at?: string;
  created_at: string;
}

export interface ApiKeyCreatePayload {
  name: string;
  permissions: string[];
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  key: string;
  permissions: string[];
}

// Webhooks
export interface Webhook {
  id: string;
  url: string;
  events: string[];
  status: string;
  last_delivery_at?: string;
  last_response_code?: number;
  created_at: string;
}

export interface WebhookCreatePayload {
  url: string;
  events: string[];
}

export interface WebhookUpdate {
  url?: string;
  events?: string[];
  status?: string;
}

// Notifications
export interface NotificationPrefs {
  preferences: Record<string, { email: boolean; in_app: boolean }>;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

export interface NotificationPrefsUpdate {
  preferences?: Record<string, { email: boolean; in_app: boolean }>;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

// Billing
export interface SettingsBilling {
  plan_name: string;
  plan_price: number;
  next_billing?: string;
  features: string[];
  payment_method?: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  };
  usage: {
    tokens: { used: number; limit: number };
    cost: number;
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
