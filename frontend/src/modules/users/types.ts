export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  role: string;
  org_id: string;
  preferences: Record<string, unknown>;
  is_active: boolean;
  mfa_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_active_at: string | null;
}

export interface OrgDetails {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  logo_url: string | null;
  max_members: number;
  created_at: string;
  updated_at: string;
}

export interface OrgMember {
  user_id: string;
  email: string;
  name: string;
  role: string;
  joined_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  is_active: boolean;
  key?: string; // only returned at creation time
}
