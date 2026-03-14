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
  ChevronLeft,
  ChevronRight,
  LogOut,
  Palette,
  Fingerprint,
  Users,
  Star,
  DollarSign,
  PieChart,
  Sparkles,
  Paintbrush,
  Puzzle,
  CheckCircle,
  Settings2,
  Headphones,
  Zap,
  UtensilsCrossed,
  Copy,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/use-sidebar";
import { useAuthStore } from "@/lib/store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
  { label: "Children's Books", href: "/specialty/childrens-books", icon: Sparkles },
  { label: "Coloring Books", href: "/specialty/coloring-books", icon: Paintbrush },
  { label: "Puzzle Books", href: "/specialty/puzzle-books", icon: Puzzle },
  { label: "Comic Books", href: "/specialty/comic-books", icon: Zap },
  { label: "Cookbooks", href: "/specialty/cookbook-books", icon: UtensilsCrossed },
  { label: "Style Clones", href: "/specialty/style-clones", icon: Copy },
  { label: "Style Profiles", href: "/style-profiles", icon: Fingerprint },
  { label: "Knowledge Vault", href: "/knowledge", icon: LibraryBig },
  { label: "Publishing", href: "/publishing", icon: BookOpen },
  { label: "Production Pipeline", href: "/pipeline", icon: Workflow },
  { label: "Marketing", href: "/marketing", icon: Megaphone },
  { label: "Product Page Lab", href: "/product-page", icon: FlaskConical },
  { label: "Advertising", href: "/advertising", icon: Target },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Pricing Automation", href: "/pricing", icon: DollarSign },
  { label: "AI Agents", href: "/agents", icon: Bot },
];

const bottomItems: NavItem[] = [
  { label: "Admin Panel", href: "/admin", icon: Settings2 },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggle } = useSidebar();
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

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "hidden md:flex flex-col border-r bg-card h-full transition-all duration-300",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-16 px-4", collapsed ? "justify-center" : "px-6")}>
          {collapsed ? (
            <span className="text-lg font-bold text-primary">SP</span>
          ) : (
            <h2 className="text-lg font-bold truncate">SelfPublisherForge</h2>
          )}
        </div>

        <Separator />

        {/* Main Navigation */}
        <nav aria-label="Main navigation" className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname?.startsWith(item.href + "/");
            const Icon = item.icon;

            const linkContent = (
              <Link
                key={item.href}
                href={item.href}
                aria-label={collapsed ? item.label : undefined}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-md text-sm font-medium transition-colors",
                  collapsed ? "justify-center px-2 py-2" : "px-3 py-2",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              );
            }

            return linkContent;
          })}
        </nav>

        <Separator />

        {/* Bottom Items */}
        <div className="px-2 py-2 space-y-1">
          {bottomItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            const linkContent = (
              <Link
                key={item.href}
                href={item.href}
                aria-label={collapsed ? item.label : undefined}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-md text-sm font-medium transition-colors",
                  collapsed ? "justify-center px-2 py-2" : "px-3 py-2",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              );
            }

            return linkContent;
          })}
        </div>

        <Separator />

        {/* User Menu */}
        <div className={cn("p-2", collapsed ? "flex flex-col items-center gap-2" : "px-4 py-3")}>
          <div className={cn("flex items-center gap-3", collapsed && "flex-col")}>
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">{userInitials}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user?.name || "User"}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user?.email || ""}
                </p>
              </div>
            )}
            {collapsed ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={logout}
                    aria-label="Sign out"
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Sign out</TooltipContent>
              </Tooltip>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0"
                onClick={logout}
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Collapse Toggle */}
        <Separator />
        <div className="p-2 flex justify-center">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggle}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
