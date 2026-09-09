"use client";

import { ProfileForm } from "@/modules/users/components/ProfileForm";
import { DangerZone } from "@/modules/users/components/DangerZone";
import { PenNamesSection } from "@/modules/pen_names";
import { Separator } from "@/components/ui/separator";
import { useTranslations } from "@/hooks/use-translations";

export default function ProfileSettingsPage() {
  const t = useTranslations("settings.profile");
  return (
    <div className="space-y-6">
      <div>
        <h2 id="profile-settings-heading" className="text-lg font-semibold">
          {t("heading")}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t("description")}
        </p>
      </div>

      <section
        aria-labelledby="profile-settings-heading"
        className="rounded-lg border bg-card p-6"
      >
        <ProfileForm />
      </section>

      <Separator />

      <section
        aria-labelledby="pen-names-heading"
        className="rounded-lg border bg-card p-6"
      >
        <PenNamesSection />
      </section>

      <Separator />

      <DangerZone />
    </div>
  );
}
