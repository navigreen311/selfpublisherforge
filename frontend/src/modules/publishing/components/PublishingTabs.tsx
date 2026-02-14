"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { lazyLoadNamed } from "@/lib/lazy";

const AccountsTab = lazyLoadNamed(
  () => import("@/modules/publishing/components/AccountsTab"),
  "AccountsTab"
);
const ExportsTab = lazyLoadNamed(
  () => import("@/modules/publishing/components/ExportsTab"),
  "ExportsTab"
);
const ListingsTab = lazyLoadNamed(
  () => import("@/modules/publishing/components/ListingsTab"),
  "ListingsTab"
);
const ISBNsTab = lazyLoadNamed(
  () => import("@/modules/publishing/components/ISBNsTab"),
  "ISBNsTab"
);
const PricingTab = lazyLoadNamed(
  () => import("@/modules/publishing/components/PricingTab"),
  "PricingTab"
);

const TAB_VALUES = ["accounts", "exports", "listings", "isbns", "pricing"] as const;
type TabValue = (typeof TAB_VALUES)[number];

interface PublishingTabsProps {
  defaultTab?: string;
}

export function PublishingTabs({ defaultTab = "accounts" }: PublishingTabsProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const currentTab = (searchParams.get("tab") as TabValue) || defaultTab;

  const handleTabChange = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("tab", value);
      router.replace(`${pathname}?${params.toString()}`);
    },
    [searchParams, router, pathname]
  );

  return (
    <Tabs value={currentTab} onValueChange={handleTabChange}>
      <TabsList>
        <TabsTrigger value="accounts">Accounts</TabsTrigger>
        <TabsTrigger value="exports">Exports</TabsTrigger>
        <TabsTrigger value="listings">Listings</TabsTrigger>
        <TabsTrigger value="isbns">ISBNs</TabsTrigger>
        <TabsTrigger value="pricing">Pricing</TabsTrigger>
      </TabsList>

      <TabsContent value="accounts">
        <AccountsTab />
      </TabsContent>
      <TabsContent value="exports">
        <ExportsTab />
      </TabsContent>
      <TabsContent value="listings">
        <ListingsTab />
      </TabsContent>
      <TabsContent value="isbns">
        <ISBNsTab />
      </TabsContent>
      <TabsContent value="pricing">
        <PricingTab />
      </TabsContent>
    </Tabs>
  );
}
