"use client";

import { useState } from "react";
import { AccountCard } from "@/modules/publishing/components/AccountCard";
import { ListingTable } from "@/modules/publishing/components/ListingTable";
import {
  usePublishingAccounts,
  useCreateAccount,
  type CreateAccountPayload,
} from "@/modules/publishing/hooks";
import { toast } from "sonner";
import Link from "next/link";

const PLATFORMS = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "draft2digital", label: "Draft2Digital" },
  { value: "smashwords", label: "Smashwords" },
  { value: "apple_books", label: "Apple Books" },
  { value: "barnes_noble", label: "Barnes & Noble" },
  { value: "kobo", label: "Kobo" },
  { value: "google_play", label: "Google Play Books" },
];

export default function PublishingDashboardPage() {
  const { data: accounts = [], isLoading: accountsLoading } = usePublishingAccounts();
  const createAccount = useCreateAccount();

  const [showConnect, setShowConnect] = useState(false);
  const [newPlatform, setNewPlatform] = useState("kdp");
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

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
      },
      onError: () => toast.error("Failed to connect account"),
    });
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Publishing Operations</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your publishing accounts, export manuscripts, and track listings.
          </p>
        </div>
        <Link
          href="/publishing/export"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          New Export
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          href="/publishing/export"
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900">Export Manuscript</h3>
          <p className="mt-1 text-sm text-gray-500">
            Generate EPUB or print-ready PDF with formatting templates
          </p>
        </Link>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900">Connected Accounts</h3>
          <p className="mt-1 text-3xl font-bold text-indigo-600">{accounts.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900">Active Listings</h3>
          <p className="mt-1 text-3xl font-bold text-green-600">0</p>
        </div>
      </div>

      {/* Publishing Accounts */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Publishing Accounts</h2>
          <button
            onClick={() => setShowConnect(!showConnect)}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            {showConnect ? "Cancel" : "+ Connect Account"}
          </button>
        </div>

        {showConnect && (
          <form
            onSubmit={handleConnect}
            className="mb-6 rounded-lg border border-indigo-200 bg-indigo-50 p-5 space-y-4"
          >
            <h3 className="font-medium text-gray-900">Connect New Account</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
                <select
                  value={newPlatform}
                  onChange={(e) => setNewPlatform(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  {PLATFORMS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                  placeholder="My KDP Account"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={createAccount.isPending}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {createAccount.isPending ? "Connecting..." : "Connect"}
              </button>
            </div>
          </form>
        )}

        {accountsLoading ? (
          <div className="py-8 text-center text-gray-500">Loading accounts...</div>
        ) : accounts.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
            <h3 className="font-medium text-gray-900">No accounts connected</h3>
            <p className="mt-1 text-sm text-gray-500">
              Connect your first publishing platform account to get started.
            </p>
            <button
              onClick={() => setShowConnect(true)}
              className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Connect Account
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        )}
      </section>

      {/* Listings */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Listings</h2>
        <ListingTable />
      </section>
    </div>
  );
}
