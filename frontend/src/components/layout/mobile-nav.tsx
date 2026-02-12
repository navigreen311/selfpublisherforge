"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderOpen,
  TrendingUp,
  PenTool,
  BookOpen,
  LibraryBig,
  Workflow,
  Megaphone,
  FlaskConical,
  Target,
  BarChart3,
  Bot,
  Settings,
  X,
  LogOut,
  Palette,
  Fingerprint,
  Users,
  Star,
  DollarSign,
  PieChart,
  CheckCircle,
  Settings2,
  Headphones,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/use-sidebar";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Projects", href: "/projects", icon: FolderOpen },
  { label: "Market Research", href: "/market", icon: TrendingUp },
  { label: "Competitor Finder", href: "/competitors", icon: Users },
  { label: "Review Intelligence", href: "/reviews", icon: Star },
  { label: "Writing Studio", href: "/writing", icon: PenTool },
  { label: "Cover Design Studio", href: "/cover-design", icon: Palette },
  { label: "Audiobook Studio", href: "/audiobook-studio", icon: Headphones },
  { label: "Style Profiles", href: "/style-profiles", icon: Fingerprint },
  { label: "Knowledge Vault", href: "/knowledge", icon: LibraryBig },
  { label: "Publishing", href: "/publishing", icon: BookOpen },
  { label: "KDP Validation", href: "/publishing/validation", icon: CheckCircle },
  { label: "Production Pipeline", href: "/pipeline", icon: Workflow },
  { label: "Marketing", href: "/marketing", icon: Megaphone },
  { label: "Product Page Lab", href: "/product-page", icon: FlaskConical },
  { label: "Advertising", href: "/advertising", icon: Target },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Portfolio Economics", href: "/analytics/portfolio", icon: PieChart },
  { label: "Pricing Automation", href: "/pricing", icon: DollarSign },
  { label: "AI Agents", href: "/agents", icon: Bot },
  { label: "Admin Panel", href: "/admin", icon: Settings2 },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();
  const { mobileOpen, closeMobile } = useSidebar();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const userInitials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  if (!mobileOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50 md:hidden"
        onClick={closeMobile}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className="fixed inset-y-0 left-0 z-50 w-72 bg-card border-r flex flex-col md:hidden animate-in slide-in-from-left duration-300"
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation menu"
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4">
          <h2 className="text-lg font-bold">SelfPublisherForge</h2>
          <Button variant="ghost" size="icon" onClick={closeMobile} aria-label="Close menu">
            <X className="h-5 w-5" aria-hidden="true" />
          </Button>
        </div>

        <Separator />

        {/* Navigation */}
        <nav aria-label="Main navigation" className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname?.startsWith(item.href + "/");
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeMobile}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <Separator />

        {/* User */}
        <div className="p-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="text-xs">{userInitials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.name || "User"}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email || ""}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              aria-label="Sign out"
              onClick={() => {
                logout();
                closeMobile();
              }}
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
