"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { PageSkeleton } from "@/components/ui/skeleton";

/**
 * Settings root page — redirects to the Profile tab by default and
 * renders tab navigation that wraps individual setting pages.
 */
export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/settings/profile");
  }, [router]);

  return <PageSkeleton />;
}
