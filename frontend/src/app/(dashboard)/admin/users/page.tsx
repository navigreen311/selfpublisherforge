import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Admin - Users",
  description: "Manage user accounts, roles, and access permissions.",
  noindex: true,
});

"use client";

import { UserTable } from "@/modules/admin/components/UserTable";
import { useTranslations } from "@/hooks/use-translations";

export default function AdminUsersPage() {
  const t = useTranslations("admin");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">{t("users.title")}</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("users.subtitle")}
        </p>
      </div>
      <UserTable />
    </div>
  );
}
