/**
 * Permission module definitions used by the Custom Role Builder.
 * Matches Feature 2C spec (SelfPublisherForge Gaps prompt, lines 255-297).
 */
import type { PermissionAction } from "./types";

export interface PermissionModuleDef {
  key: string;
  label: string;
  category: string;
  /** Which actions are applicable to this module. */
  actions: PermissionAction[];
}

export const PERMISSION_ACTIONS: PermissionAction[] = [
  "view",
  "create",
  "edit",
  "delete",
  "publish",
];

export const PERMISSION_MODULES: PermissionModuleDef[] = [
  // Overview
  { key: "dashboard", label: "Dashboard", category: "Overview", actions: ["view"] },
  { key: "projects", label: "Projects", category: "Overview", actions: ["view", "create", "edit", "delete"] },

  // Research
  { key: "market_research", label: "Market Research", category: "Research", actions: ["view", "create", "edit", "delete"] },
  { key: "competitor_finder", label: "Competitor Finder", category: "Research", actions: ["view", "create", "edit", "delete"] },
  { key: "review_intelligence", label: "Review Intelligence", category: "Research", actions: ["view", "create", "edit", "delete"] },

  // Content studios
  { key: "writing_studio", label: "Writing Studio", category: "Content", actions: ["view", "create", "edit", "delete"] },
  { key: "cover_design_studio", label: "Cover Design Studio", category: "Content", actions: ["view", "create", "edit", "delete"] },
  { key: "audiobook_studio", label: "Audiobook Studio", category: "Content", actions: ["view", "create", "edit", "delete"] },

  // Specialty books
  { key: "childrens_books", label: "Children's Books", category: "Specialty Books", actions: ["view", "create", "edit", "delete", "publish"] },
  { key: "coloring_books", label: "Coloring Books", category: "Specialty Books", actions: ["view", "create", "edit", "delete", "publish"] },
  { key: "puzzle_books", label: "Puzzle Books", category: "Specialty Books", actions: ["view", "create", "edit", "delete", "publish"] },
  { key: "comic_books", label: "Comic Books", category: "Specialty Books", actions: ["view", "create", "edit", "delete", "publish"] },
  { key: "cookbooks", label: "Cookbooks", category: "Specialty Books", actions: ["view", "create", "edit", "delete", "publish"] },

  // Production
  { key: "style_profiles", label: "Style Profiles", category: "Production", actions: ["view", "create", "edit", "delete"] },
  { key: "production_pipeline", label: "Production Pipeline", category: "Production", actions: ["view", "create", "edit", "delete"] },

  // Go-to-market
  { key: "marketing", label: "Marketing", category: "Go-to-market", actions: ["view", "create", "edit", "delete"] },
  { key: "publishing", label: "Publishing", category: "Go-to-market", actions: ["view", "create", "edit", "delete", "publish"] },
  { key: "advertising", label: "Advertising", category: "Go-to-market", actions: ["view", "create", "edit", "delete"] },

  // Analytics
  { key: "analytics_content", label: "Analytics (Content)", category: "Analytics", actions: ["view"] },
  { key: "analytics_revenue", label: "Analytics (Revenue)", category: "Analytics", actions: ["view"] },
  { key: "pricing", label: "Pricing", category: "Analytics", actions: ["view", "create", "edit", "delete"] },

  // System
  { key: "ai_agents", label: "AI Agents", category: "System", actions: ["view", "create", "edit", "delete"] },
  { key: "admin_panel", label: "Admin Panel", category: "System", actions: ["view", "create", "edit", "delete"] },
  { key: "settings", label: "Settings", category: "System", actions: ["view", "edit"] },
  { key: "team_management", label: "Team Management", category: "System", actions: ["view", "create", "edit", "delete"] },
  { key: "billing", label: "Billing", category: "System", actions: ["view", "create", "edit", "delete"] },
];

export const MODULE_CATEGORIES: string[] = Array.from(
  new Set(PERMISSION_MODULES.map((m) => m.category))
);

export function emptyPermissions() {
  const perms: Record<string, Partial<Record<PermissionAction, boolean>>> = {};
  for (const mod of PERMISSION_MODULES) {
    perms[mod.key] = {};
    for (const action of mod.actions) perms[mod.key][action] = false;
  }
  return perms;
}

export const BUILT_IN_ROLE_ICONS: Record<string, string> = {
  Owner: "👑",
  Admin: "🔧",
  Editor: "✏️",
  Designer: "🎨",
  Viewer: "👀",
  VA: "🤖",
};
