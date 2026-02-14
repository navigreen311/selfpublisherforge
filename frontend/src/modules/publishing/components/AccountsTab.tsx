"use client";

import { useState, useMemo } from "react";
import { AccountCard } from "./AccountCard";
import {
  usePublishingAccounts,
  useCreateAccount,
  type CreateAccountPayload,
} from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  PUBLISHING_PLATFORMS,
  PUBLISHING_PLATFORM_COLORS,
} from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

export function AccountsTab() {
  const t = useTranslations("publishing");
  const { data: accounts = [], isLoading: accountsLoading } =
    usePublishingAccounts();
  const createAccount = useCreateAccount();

  const [showConnect, setShowConnect] = useState(false);
  const [newPlatform, setNewPlatform] = useState(
    PUBLISHING_PLATFORMS[0].value,
  );
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [connectTouched, setConnectTouched] = useState<
    Record<string, boolean>
  >({});
  const [connectSubmitAttempted, setConnectSubmitAttempted] = useState(false);

  // Platforms the user hasn't connected yet
  const connectedPlatformSet = useMemo(
    () => new Set(accounts.map((a) => a.platform)),
    [accounts],
  );

  const availablePlatforms = useMemo(
    () => PUBLISHING_PLATFORMS.filter((p) => !connectedPlatformSet.has(p.value)),
    [connectedPlatformSet],
  );

  // ---------- Connect form validation ----------
  const connectErrors: Record<string, string> = {};
  if (!newName.trim())
    connectErrors.name = t("accounts.connectForm.errors.nameRequired");
  if (
    newEmail.trim() &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail.trim())
  )
    connectErrors.email = t("accounts.connectForm.errors.emailInvalid");

  const showConnectError = (field: string): boolean =>
    !!(connectErrors[field] && (connectTouched[field] || connectSubmitAttempted));

  const connectErrorClass = (field: string): string =>
    showConnectError(field)
      ? "border-red-500 focus:border-red-500 focus:ring-red-500"
      : "border focus:border-indigo-500 focus:ring-indigo-500";

  const connectHasErrors = Object.keys(connectErrors).length > 0;

  const resetForm = () => {
    setShowConnect(false);
    setNewName("");
    setNewEmail("");
    setNewPlatform(PUBLISHING_PLATFORMS[0].value);
    setConnectTouched({});
    setConnectSubmitAttempted(false);
  };

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
        resetForm();
      },
      onError: () => toast.error("Failed to connect account"),
    });
  };

  const handleQuickConnect = (platformValue: string) => {
    setNewPlatform(platformValue);
    setShowConnect(true);
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-foreground">
            {t("accounts.title")}
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
            Manage your publishing platform connections
          </p>
        </div>
        <button
          onClick={() => setShowConnect(!showConnect)}
          aria-expanded={showConnect}
          aria-label={
            showConnect
              ? "Cancel connecting account"
              : "Connect a new publishing account"
          }
          className="w-full sm:w-auto rounded-md bg-indigo-600 px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-indigo-700 text-center"
        >
          {showConnect ? t("accounts.cancel") : `+ ${t("accounts.connectAccount")}`}
        </button>
      </div>

      {/* Connect Form */}
      {showConnect && (
        <form
          onSubmit={handleConnect}
          aria-label="Connect new publishing account"
          className="rounded-lg border border-indigo-200 bg-indigo-50 p-4 sm:p-5 space-y-3 sm:space-y-4"
        >
          <h3 className="text-sm sm:text-base font-medium text-foreground">
            {t("accounts.connectForm.title")}
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-3">
            <div>
              <label
                htmlFor="connect-platform"
                className="block text-sm font-medium text-foreground mb-1"
              >
                {t("accounts.connectForm.platform")}
              </label>
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
              <label
                htmlFor="connect-account-name"
                className="block text-sm font-medium text-foreground mb-1"
              >
                {t("accounts.connectForm.accountNameRequired")}
              </label>
              <input
                id="connect-account-name"
                type="text"
                required
                aria-required="true"
                aria-invalid={
                  showConnectError("name") ? "true" : undefined
                }
                aria-describedby={
                  showConnectError("name")
                    ? "connect-name-error"
                    : undefined
                }
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onBlur={() =>
                  setConnectTouched((prev) => ({ ...prev, name: true }))
                }
                placeholder="My Publishing Account"
                className={`w-full rounded-md border px-3 py-2 text-sm ${connectErrorClass("name")}`}
              />
              {showConnectError("name") && (
                <p
                  id="connect-name-error"
                  role="alert"
                  className="mt-1 text-xs text-red-500"
                >
                  {connectErrors.name}
                </p>
              )}
            </div>
            <div>
              <label
                htmlFor="connect-email"
                className="block text-sm font-medium text-foreground mb-1"
              >
                {t("accounts.connectForm.email")}
              </label>
              <input
                id="connect-email"
                type="email"
                aria-invalid={
                  showConnectError("email") ? "true" : undefined
                }
                aria-describedby={
                  showConnectError("email")
                    ? "connect-email-error"
                    : undefined
                }
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                onBlur={() =>
                  setConnectTouched((prev) => ({ ...prev, email: true }))
                }
                placeholder={t("accounts.connectForm.optional")}
                className={`w-full rounded-md border px-3 py-2 text-sm ${connectErrorClass("email")}`}
              />
              {showConnectError("email") && (
                <p
                  id="connect-email-error"
                  role="alert"
                  className="mt-1 text-xs text-red-500"
                >
                  {connectErrors.email}
                </p>
              )}
            </div>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={createAccount.isPending || connectHasErrors}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createAccount.isPending
                ? t("accounts.connectForm.connecting")
                : t("accounts.connectForm.connect")}
            </button>
          </div>
        </form>
      )}

      {/* Connected Accounts */}
      <section aria-labelledby="connected-accounts-heading">
        <h3
          id="connected-accounts-heading"
          className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4"
        >
          Connected Accounts
          {!accountsLoading && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({accounts.length})
            </span>
          )}
        </h3>

        {accountsLoading ? (
          <div
            className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-busy="true"
            aria-label="Loading publishing accounts"
          >
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-28 sm:h-32" />
            ))}
          </div>
        ) : accounts.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border p-6 sm:p-8 text-center">
            <h4 className="text-sm sm:text-base font-medium text-foreground">
              {t("accounts.empty.title")}
            </h4>
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

      {/* Available Platforms */}
      {!accountsLoading && availablePlatforms.length > 0 && (
        <section aria-labelledby="available-platforms-heading">
          <h3
            id="available-platforms-heading"
            className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4"
          >
            Available Platforms
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({availablePlatforms.length})
            </span>
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {availablePlatforms.map((platform) => {
              const colorClass =
                PUBLISHING_PLATFORM_COLORS[platform.value] ||
                "bg-gray-100 text-gray-800";
              return (
                <div
                  key={platform.value}
                  className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${colorClass}`}
                    >
                      {platform.label}
                    </span>
                  </div>
                  <button
                    onClick={() => handleQuickConnect(platform.value)}
                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
                  >
                    Connect
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
