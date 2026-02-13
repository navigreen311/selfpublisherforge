
"use client";

import { OrgTable } from "@/modules/admin/components/OrgTable";
import { useTranslations } from "@/hooks/use-translations";

export default function AdminOrganizationsPage() {
  const t = useTranslations("admin");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">{t("organizations.title")}</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("organizations.subtitle")}
        </p>
      </div>
      <OrgTable />
    </div>
  );
}
