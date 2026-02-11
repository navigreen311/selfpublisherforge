import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Publishing",
  description: "Connect and manage your publishing accounts across Amazon KDP, IngramSpark, Draft2Digital, and more platforms.",
  noindex: true,
});

"use client";

import { useState } from "react";
import { AccountCard } from "@/modules/publishing/components/AccountCard";
import { ListingTable } from "@/modules/publishing/components/ListingTable";
import {
  usePublishingAccounts,
  useCreateAccount,
  useListings,
  type CreateAccountPayload,
} from "@/modules/publishing/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import Link from "next/link";
import { PUBLISHING_PLATFORMS } from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

export default function PublishingDashboardPage() {
  const t = useTranslations("publishing");
  const { data: accounts = [], isLoading: accountsLoading } = usePublishingAccounts();
  const { data: listings = [], isLoading: listingsLoading, isError: listingsError } = useListings();
  const createAccount = useCreateAccount();

  const activeListingsCount = listings.filter((l) => l.status === "active").length;

  const [showConnect, setShowConnect] = useState(false);
  const [newPlatform, setNewPlatform] = useState(PUBLISHING_PLATFORMS[0].value);
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [connectTouched, setConnectTouched] = useState<Record<string, boolean>>({});
  const [connectSubmitAttempted, setConnectSubmitAttempted] = useState(false);

  // Simple validation for connect form
  const connectErrors: Record<string, string> = {};
  if (!newName.trim()) connectErrors.name = t("accounts.connectForm.errors.nameRequired");
  if (newEmail.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail.trim()))
    connectErrors.email = t("accounts.connectForm.errors.emailInvalid");

  const showConnectError = (field: string): boolean =>
    !!(connectErrors[field] && (connectTouched[field] || connectSubmitAttempted));

  const connectErrorClass = (field: string): string =>
    showConnectError(field)
      ? "border-red-500 focus:border-red-500 focus:ring-red-500"
      : "border focus:border-indigo-500 focus:ring-indigo-500";

  const connectHasErrors = Object.keys(connectErrors).length > 0;

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    setConnectSubmitAttempted(true);

    if (Object.keys(connectErrors).length > 0) {
      toast.error(Object.values(connectErrors)[0]);
      return;
    }

    const payload: CreateAccountPayload = {
      platform: newPlatform,
      account_name: newName.trim(),
      account_email: newEmail.trim() || undefined,
    };

    createAccount.mutate(payload, {
      onSuccess: () => {
        toast.success("Account connected");
        setShowConnect(false);
        setNewName("");
        setNewEmail("");
        setConnectTouched({});
        setConnectSubmitAttempted(false);
      },
      onError: () => toast.error("Failed to connect account"),
    });
  };

  return (
    <div className="space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-foreground">{t("title")}</h1>
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>
        <Link
          href="/publishing/export"
          className="w-full sm:w-auto rounded-md bg-indigo-600 px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-indigo-700 text-center"
        >
          {t("newExport")}
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-3">
        <Link
          href="/publishing/export"
          className="rounded-lg border bg-card p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="text-sm sm:text-base font-semibold text-foreground">{t("quickActions.exportManuscript.title")}</h3>
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
            {t("quickActions.exportManuscript.description")}
          </p>
        </Link>
        <div className="rounded-lg border bg-card p-4 sm:p-5 shadow-sm">
          <h3 className="text-sm sm:text-base font-semibold text-foreground">{t("quickActions.connectedAccounts.title")}</h3>
          <p className="mt-1 text-2xl sm:text-3xl font-bold text-indigo-600">{accounts.length}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 sm:p-5 shadow-sm">
          <h3 className="text-sm sm:text-base font-semibold text-foreground">{t("quickActions.activeListings.title")}</h3>
          {listingsLoading ? (
            <Skeleton className="mt-1 h-8 sm:h-10 w-16 sm:w-20" />
          ) : listingsError ? (
            <p className="mt-1 text-xs sm:text-sm text-red-500">{t("quickActions.activeListings.failedToLoad")}</p>
          ) : (
            <p className="mt-1 text-2xl sm:text-3xl font-bold text-green-600">{activeListingsCount}</p>
          )}
        </div>
      </div>

      {/* Publishing Accounts */}
      <section aria-labelledby="publishing-accounts-heading">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h2 id="publishing-accounts-heading" className="text-base sm:text-lg font-semibold text-foreground">{t("accounts.title")}</h2>
          <button
            onClick={() => setShowConnect(!showConnect)}
            aria-expanded={showConnect}
            aria-label={showConnect ? "Cancel connecting account" : "Connect a new publishing account"}
            className="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            {showConnect ? t("accounts.cancel") : `+ ${t("accounts.connectAccount")}`}
          </button>
        </div>

        {showConnect && (
          <form
            onSubmit={handleConnect}
            aria-label="Connect new publishing account"
            className="mb-4 sm:mb-6 rounded-lg border border-indigo-200 bg-indigo-50 p-4 sm:p-5 space-y-3 sm:space-y-4"
          >
            <h3 className="text-sm sm:text-base font-medium text-foreground">{t("accounts.connectForm.title")}</h3>
            <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-3">
              <div>
                <label htmlFor="connect-platform" className="block text-sm font-medium text-foreground mb-1">{t("accounts.connectForm.platform")}</label>
                <select
                  id="connect-platform"
                  value={newPlatform}
                  onChange={(e) => setNewPlatform(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                >
                  {PUBLISHING_PLATFORMS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="connect-account-name" className="block text-sm font-medium text-foreground mb-1">
                  {t("accounts.connectForm.accountNameRequired")}
                </label>
                <input
                  id="connect-account-name"
                  type="text"
                  required
                  aria-required="true"
                  aria-invalid={showConnectError("name") ? "true" : undefined}
                  aria-describedby={showConnectError("name") ? "connect-name-error" : undefined}
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onBlur={() => setConnectTouched((prev) => ({ ...prev, name: true }))}
                  placeholder="My Publishing Account"
                  className={`w-full rounded-md border px-3 py-2 text-sm ${connectErrorClass("name")}`}
                />
                {showConnectError("name") && (
                  <p id="connect-name-error" role="alert" className="mt-1 text-xs text-red-500">{connectErrors.name}</p>
                )}
              </div>
              <div>
                <label htmlFor="connect-email" className="block text-sm font-medium text-foreground mb-1">{t("accounts.connectForm.email")}</label>
                <input
                  id="connect-email"
                  type="email"
                  aria-invalid={showConnectError("email") ? "true" : undefined}
                  aria-describedby={showConnectError("email") ? "connect-email-error" : undefined}
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  onBlur={() => setConnectTouched((prev) => ({ ...prev, email: true }))}
                  placeholder={t("accounts.connectForm.optional")}
                  className={`w-full rounded-md border px-3 py-2 text-sm ${connectErrorClass("email")}`}
                />
                {showConnectError("email") && (
                  <p id="connect-email-error" role="alert" className="mt-1 text-xs text-red-500">{connectErrors.email}</p>
                )}
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={createAccount.isPending || connectHasErrors}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createAccount.isPending ? t("accounts.connectForm.connecting") : t("accounts.connectForm.connect")}
              </button>
            </div>
          </form>
        )}

        {accountsLoading ? (
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Loading publishing accounts">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-28 sm:h-32" />
            ))}
          </div>
        ) : accounts.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border p-6 sm:p-8 text-center">
            <h3 className="text-sm sm:text-base font-medium text-foreground">{t("accounts.empty.title")}</h3>
            <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
              {t("accounts.empty.description")}
            </p>
            <button
              onClick={() => setShowConnect(true)}
              aria-label="Connect your first publishing account"
              className="mt-3 sm:mt-4 rounded-md bg-indigo-600 px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-indigo-700"
            >
              {t("accounts.empty.action")}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        )}
      </section>

      {/* Listings */}
      <section aria-labelledby="listings-heading">
        <h2 id="listings-heading" className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">{t("listings.title")}</h2>
        <div className="overflow-x-auto -mx-4 sm:mx-0">
          <ListingTable />
        </div>
      </section>
    </div>
  );
}
