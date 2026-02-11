"use client";

import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function Home() {
  const t = useTranslations("home");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">{t("title")}</h1>
      <p className="text-muted-foreground text-lg mb-8">
        {t("subtitle")}
      </p>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:opacity-90"
        >
          {t("signIn")}
        </Link>
        <Link
          href="/register"
          className="border border-border px-6 py-3 rounded-lg hover:bg-accent"
        >
          {t("getStarted")}
        </Link>
      </div>
    </main>
  );
}
