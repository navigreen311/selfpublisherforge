"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "Projects", href: "/projects", icon: "FolderOpen" },
  { label: "Market Research", href: "/market", icon: "TrendingUp" },
  { label: "Writing Studio", href: "/writing", icon: "PenTool" },
  { label: "Publishing", href: "/publishing", icon: "BookOpen" },
  { label: "Marketing", href: "/marketing", icon: "Megaphone" },
  { label: "Advertising", href: "/advertising", icon: "Target" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "AI Agents", href: "/agents", icon: "Bot" },
  { label: "Settings", href: "/settings", icon: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-card h-full flex flex-col">
      <div className="p-6">
        <h2 className="text-lg font-bold">SelfPublisherForge</h2>
      </div>
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              pathname === item.href
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
