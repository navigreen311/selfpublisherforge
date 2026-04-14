"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  FolderOpen,
  TrendingUp,
  PenTool,
  BookOpen,
  Megaphone,
  BarChart3,
  Bot,
  Settings,
  DollarSign,
  Plus,
  FileText,
  Sparkles,
  Activity,
  Bell,
} from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { VisuallyHidden } from "@/components/shared/VisuallyHidden";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface CommandItem {
  id: string;
  label: string;
  hint?: string;
  group: "Quick Actions" | "Pages" | "Results" | "Recent";
  icon?: React.ComponentType<{ className?: string }>;
  action: () => void;
}

const RECENT_KEY = "spf.cmdk.recent";

function loadRecent(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
  } catch {
    return [];
  }
}

function pushRecent(id: string) {
  if (typeof window === "undefined") return;
  const existing = loadRecent().filter((x) => x !== id);
  existing.unshift(id);
  localStorage.setItem(RECENT_KEY, JSON.stringify(existing.slice(0, 8)));
}

function fuzzyMatch(query: string, text: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t.includes(q)) return true;
  // sequential subsequence
  let qi = 0;
  for (let i = 0; i < t.length && qi < q.length; i++) {
    if (t[i] === q[qi]) qi++;
  }
  return qi === q.length;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: Props) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [remoteResults, setRemoteResults] = useState<CommandItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const go = useCallback(
    (id: string, path: string) => {
      pushRecent(id);
      onOpenChange(false);
      setQuery("");
      router.push(path);
    },
    [onOpenChange, router]
  );

  const baseItems = useMemo<CommandItem[]>(
    () => [
      // Quick actions
      { id: "act:new-project", label: "Create New Project", group: "Quick Actions", icon: Plus, action: () => go("act:new-project", "/projects?new=1") },
      { id: "act:new-childrens", label: "Create Children's Book", group: "Quick Actions", icon: Plus, action: () => go("act:new-childrens", "/specialty-books") },
      { id: "act:new-coloring", label: "Create Coloring Book", group: "Quick Actions", icon: Plus, action: () => go("act:new-coloring", "/specialty-books") },
      { id: "act:new-puzzle", label: "Create Puzzle Book", group: "Quick Actions", icon: Plus, action: () => go("act:new-puzzle", "/specialty/puzzle-books/new") },
      { id: "act:settings", label: "Open Settings", group: "Quick Actions", icon: Settings, action: () => go("act:settings", "/settings") },
      { id: "act:analytics", label: "View Analytics", group: "Quick Actions", icon: BarChart3, action: () => go("act:analytics", "/analytics") },
      // Pages
      { id: "pg:dashboard", label: "Dashboard", group: "Pages", icon: LayoutDashboard, action: () => go("pg:dashboard", "/dashboard") },
      { id: "pg:projects", label: "Projects", group: "Pages", icon: FolderOpen, action: () => go("pg:projects", "/projects") },
      { id: "pg:market", label: "Market Research", group: "Pages", icon: TrendingUp, action: () => go("pg:market", "/market") },
      { id: "pg:writing", label: "Writing Studio", group: "Pages", icon: PenTool, action: () => go("pg:writing", "/writing") },
      { id: "pg:publishing", label: "Publishing", group: "Pages", icon: BookOpen, action: () => go("pg:publishing", "/publishing") },
      { id: "pg:marketing", label: "Marketing", group: "Pages", icon: Megaphone, action: () => go("pg:marketing", "/marketing") },
      { id: "pg:advertising", label: "Advertising", group: "Pages", icon: Megaphone, action: () => go("pg:advertising", "/advertising") },
      { id: "pg:analytics", label: "Analytics", group: "Pages", icon: BarChart3, action: () => go("pg:analytics", "/analytics") },
      { id: "pg:agents", label: "AI Agents", group: "Pages", icon: Bot, action: () => go("pg:agents", "/agents") },
      { id: "pg:pricing", label: "Pricing", group: "Pages", icon: DollarSign, action: () => go("pg:pricing", "/pricing") },
      { id: "pg:style", label: "Style Profiles", group: "Pages", icon: Sparkles, action: () => go("pg:style", "/style-profiles") },
      { id: "pg:reviews", label: "Review Intelligence", group: "Pages", icon: FileText, action: () => go("pg:reviews", "/reviews") },
      { id: "pg:activity", label: "Activity Log", group: "Pages", icon: Activity, action: () => go("pg:activity", "/activity") },
      { id: "pg:notifications", label: "Notifications", group: "Pages", icon: Bell, action: () => go("pg:notifications", "/notifications") },
      { id: "pg:settings", label: "Settings", group: "Pages", icon: Settings, action: () => go("pg:settings", "/settings") },
      { id: "pg:integrations", label: "Integrations", group: "Pages", icon: Settings, action: () => go("pg:integrations", "/settings/integrations") },
    ],
    [go]
  );

  // Remote search
  useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (q.length < 2) {
      setRemoteResults([]);
      return;
    }
    const ctl = new AbortController();
    const t = setTimeout(async () => {
      try {
        const res = await api.get(`/api/v1/search`, {
          params: { q, types: "projects,books,chapters,recipes" },
          signal: ctl.signal,
        });
        const data = res.data as { results?: Array<{ id: string; type: string; title: string; url?: string }> };
        const mapped: CommandItem[] = (data.results || []).slice(0, 20).map((r) => ({
          id: `remote:${r.type}:${r.id}`,
          label: r.title,
          hint: r.type,
          group: "Results",
          icon: FileText,
          action: () => go(`remote:${r.type}:${r.id}`, r.url || `/projects/${r.id}`),
        }));
        setRemoteResults(mapped);
      } catch {
        /* ignore */
      }
    }, 180);
    return () => {
      ctl.abort();
      clearTimeout(t);
    };
  }, [query, open, go]);

  const recentIds = useMemo(() => loadRecent(), [open]);

  const filtered = useMemo<CommandItem[]>(() => {
    const q = query.trim();
    const filteredBase = baseItems.filter((i) => fuzzyMatch(q, i.label));
    if (!q) {
      // Show recents first
      const recentItems = recentIds
        .map((id) => baseItems.find((b) => b.id === id))
        .filter((x): x is CommandItem => !!x)
        .map((b) => ({ ...b, group: "Recent" as const }));
      const seen = new Set(recentItems.map((r) => r.id));
      const rest = filteredBase.filter((b) => !seen.has(b.id));
      return [...recentItems, ...rest];
    }
    return [...filteredBase, ...remoteResults];
  }, [query, baseItems, recentIds, remoteResults]);

  useEffect(() => setActiveIndex(0), [query, open]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 20);
    }
  }, [open]);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      filtered[activeIndex]?.action();
    }
  };

  // Group the results for display
  const groups: Record<string, CommandItem[]> = {};
  filtered.forEach((item) => {
    groups[item.group] = groups[item.group] || [];
    groups[item.group].push(item);
  });
  const groupOrder = ["Recent", "Results", "Quick Actions", "Pages"];

  let runningIndex = -1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 max-w-2xl overflow-hidden">
        <VisuallyHidden>
          <DialogTitle>Command Palette</DialogTitle>
        </VisuallyHidden>
        <div className="flex items-center gap-2 border-b px-4 py-3">
          <Search className="h-4 w-4 text-muted-foreground" aria-hidden />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKey}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-muted-foreground"
            aria-label="Command palette search"
          />
          <kbd className="text-xs text-muted-foreground border rounded px-1.5 py-0.5">Esc</kbd>
        </div>
        <div className="max-h-[60vh] overflow-y-auto py-2">
          {filtered.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              No results found.
            </div>
          )}
          {groupOrder.map((group) => {
            const items = groups[group];
            if (!items || items.length === 0) return null;
            return (
              <div key={group} className="mb-2">
                <div className="px-4 py-1 text-xs font-medium text-muted-foreground uppercase">
                  {group}
                </div>
                {items.map((item) => {
                  runningIndex++;
                  const idx = runningIndex;
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => item.action()}
                      onMouseEnter={() => setActiveIndex(idx)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-2 text-sm text-left",
                        idx === activeIndex
                          ? "bg-accent text-accent-foreground"
                          : "hover:bg-accent/50"
                      )}
                    >
                      {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
                      <span className="flex-1">{item.label}</span>
                      {item.hint && (
                        <span className="text-xs text-muted-foreground">{item.hint}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
