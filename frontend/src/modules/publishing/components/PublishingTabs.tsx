"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AccountCard } from "./AccountCard";
import { ListingTable } from "./ListingTable";
import type { PublishingAccount } from "../types";
import { Skeleton } from "@/components/ui/skeleton";

interface PublishingTabsProps {
  accounts: PublishingAccount[];
  accountsLoading: boolean;
}

export function PublishingTabs({ accounts, accountsLoading }: PublishingTabsProps) {
  return (
    <Tabs defaultValue="listings" className="w-full">
      <TabsList>
        <TabsTrigger value="listings">Listings</TabsTrigger>
        <TabsTrigger value="accounts">
          Accounts{accounts.length > 0 && ` (${accounts.length})`}
        </TabsTrigger>
      </TabsList>

      <TabsContent value="listings">
        <div className="overflow-x-auto -mx-4 sm:mx-0">
          <ListingTable />
        </div>
      </TabsContent>

      <TabsContent value="accounts">
        {accountsLoading ? (
          <div
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-busy="true"
            aria-label="Loading publishing accounts"
          >
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        ) : accounts.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed p-8 text-center">
            <h3 className="text-base font-medium text-foreground">
              No accounts connected
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Connect your first publishing platform account to get started.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        )}
      </TabsContent>
    </Tabs>
  );
}
