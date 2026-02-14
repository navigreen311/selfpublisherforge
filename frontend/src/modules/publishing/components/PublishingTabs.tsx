"use client";

import dynamic from "next/dynamic";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

function TabSkeleton() {
  return (
    <div className="space-y-4 py-4">
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-4 w-72" />
      <Skeleton className="h-40 w-full rounded-lg" />
    </div>
  );
}

const AccountsTab = dynamic(
  () => import("./AccountsTab").then((mod) => ({ default: mod.AccountsTab })),
  { loading: () => <TabSkeleton /> }
);

const ExportsTab = dynamic(
  () => import("./ExportsTab").then((mod) => ({ default: mod.ExportsTab })),
  { loading: () => <TabSkeleton /> }
);

const ListingsTab = dynamic(
  () => import("./ListingsTab").then((mod) => ({ default: mod.ListingsTab })),
  { loading: () => <TabSkeleton /> }
);

const ISBNsTab = dynamic(
  () => import("./ISBNsTab").then((mod) => ({ default: mod.ISBNsTab })),
  { loading: () => <TabSkeleton /> }
);

const PricingTab = dynamic(
  () => import("./PricingTab").then((mod) => ({ default: mod.PricingTab })),
  { loading: () => <TabSkeleton /> }
);

export function PublishingTabs() {
  return (
    <Tabs defaultValue="accounts" className="space-y-6">
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
