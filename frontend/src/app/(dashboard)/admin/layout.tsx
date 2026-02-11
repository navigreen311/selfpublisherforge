"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const getActiveTab = () => {
    if (pathname === "/admin") return "overview";
    if (pathname.startsWith("/admin/users")) return "users";
    if (pathname.startsWith("/admin/organizations")) return "organizations";
    if (pathname.startsWith("/admin/billing")) return "billing";
    return "overview";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Manage users, organizations, and platform settings
        </p>
      </div>

      <Tabs value={getActiveTab()} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <Link href="/admin" passHref legacyBehavior>
            <TabsTrigger value="overview" asChild>
              <a>Overview</a>
            </TabsTrigger>
          </Link>
          <Link href="/admin/users" passHref legacyBehavior>
            <TabsTrigger value="users" asChild>
              <a>Users</a>
            </TabsTrigger>
          </Link>
          <Link href="/admin/organizations" passHref legacyBehavior>
            <TabsTrigger value="organizations" asChild>
              <a>Organizations</a>
            </TabsTrigger>
          </Link>
          <Link href="/admin/billing" passHref legacyBehavior>
            <TabsTrigger value="billing" asChild>
              <a>Billing</a>
            </TabsTrigger>
          </Link>
        </TabsList>
      </Tabs>

      <div>{children}</div>
    </div>
  );
}
