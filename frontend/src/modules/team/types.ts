/** Types for Team Management & RBAC. */

export type PermissionAction =
  | "view"
  | "create"
  | "edit"
  | "delete"
  | "publish";

export type ModulePermissions = Record<PermissionAction, boolean>;
export type PermissionsMap = Record<string, Partial<ModulePermissions>>;

export interface Role {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  permissions: PermissionsMap;
  is_system: boolean;
  created_at: string;
}

export interface RoleInput {
  name: string;
  description?: string | null;
  permissions: PermissionsMap;
}

export interface TeamMember {
  user_id: string;
  email: string;
  name: string | null;
  role_id: string | null;
  role_name: string | null;
  status: string;
  joined_at: string | null;
}

export interface InvitationInput {
  email: string;
  role_id: string;
  message?: string | null;
}

export interface Invitation {
  id: string;
  org_id: string;
  email: string;
  role_id: string;
  role_name: string | null;
  status: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}
