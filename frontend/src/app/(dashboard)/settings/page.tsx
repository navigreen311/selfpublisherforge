"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

const TABS = [
  { label: "Profile", href: "/settings/profile" },
  { label: "Organization", href: "/settings/organization" },
  { label: "API Keys", href: "/settings/api-keys" },
] as const;

/**
 * Settings root page — redirects to the Profile tab by default and
 * renders tab navigation that wraps individual setting pages.
 */
export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/settings/profile");
  }, [router]);

  return null;
}
