"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
  useCurrentUser,
  type ApiKey,
} from "../hooks";

const createKeySchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  scopes: z.string().default("read"),
  expires_in_days: z.coerce.number().min(1).max(365).optional().or(z.literal("")),
});

type CreateKeyFormValues = z.infer<typeof createKeySchema>;

interface ApiKeyTableProps {
  orgId: string;
}

export function ApiKeyTable({ orgId }: ApiKeyTableProps) {
  const { data: currentUser } = useCurrentUser();
  const { data: keys, isLoading } = useApiKeys(orgId);
  const createKey = useCreateApiKey(orgId);
  const revokeKey = useRevokeApiKey(orgId);

  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [confirmRevoke, setConfirmRevoke] = useState<string | null>(null);

  const isAdminOrOwner =
    currentUser?.role === "owner" || currentUser?.role === "admin";

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateKeyFormValues>({
    resolver: zodResolver(createKeySchema),
    defaultValues: { name: "", scopes: "read", expires_in_days: "" },
  });

  const onCreateSubmit = async (values: CreateKeyFormValues) => {
    try {
      const scopes = values.scopes
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const result = await createKey.mutateAsync({
        name: values.name,
        scopes,
        expires_in_days:
          values.expires_in_days !== "" && values.expires_in_days
            ? Number(values.expires_in_days)
            : null,
      });
      if (result.key) {
        setNewKey(result.key);
      }
      toast.success("API key created");
      reset();
      setShowCreate(false);
    } catch {
      toast.error("Failed to create API key");
    }
  };

  const handleRevoke = async (keyId: string) => {
    try {
      await revokeKey.mutateAsync(keyId);
      toast.success("API key revoked");
      setConfirmRevoke(null);
    } catch {
      toast.error("Failed to revoke API key");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="h-12 bg-gray-100 rounded" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* New key banner */}
      {newKey && (
        <div className="rounded-md border border-green-200 bg-green-50 p-4">
          <p className="text-sm font-medium text-green-800 mb-1">
            Your new API key (copy it now - it will not be shown again):
          </p>
          <code className="block break-all rounded bg-white p-2 text-xs border">
            {newKey}
          </code>
          <button
            onClick={() => {
              navigator.clipboard.writeText(newKey);
              toast.success("Copied to clipboard");
            }}
            className="mt-2 text-xs text-green-700 hover:text-green-900 font-medium"
          >
            Copy to Clipboard
          </button>
          <button
            onClick={() => setNewKey(null)}
            className="mt-2 ml-4 text-xs text-gray-500 hover:text-gray-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Create form */}
      {isAdminOrOwner && (
        <div>
          {showCreate ? (
            <form
              onSubmit={handleSubmit(onCreateSubmit)}
              className="space-y-3 rounded-md border p-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Key Name
                </label>
                <input
                  {...register("name")}
                  placeholder="e.g. CI/CD Pipeline"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
                {errors.name && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.name.message}
                  </p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Scopes (comma-separated)
                  </label>
                  <input
                    {...register("scopes")}
                    placeholder="read, write"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expires in (days)
                  </label>
                  <input
                    {...register("expires_in_days")}
                    type="number"
                    placeholder="Optional"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createKey.isPending}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {createKey.isPending ? "Creating..." : "Create Key"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreate(false);
                    reset();
                  }}
                  className="rounded-md border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setShowCreate(true)}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Create New API Key
            </button>
          )}
        </div>
      )}

      {/* Keys table */}
      {!keys?.length ? (
        <p className="text-sm text-gray-500">No API keys have been created.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Prefix</th>
                <th className="pb-2 font-medium">Scopes</th>
                <th className="pb-2 font-medium">Created</th>
                <th className="pb-2 font-medium">Expires</th>
                <th className="pb-2 font-medium">Last Used</th>
                {isAdminOrOwner && (
                  <th className="pb-2 font-medium">Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {keys.map((key: ApiKey) => (
                <tr key={key.id} className="border-b last:border-0">
                  <td className="py-3 pr-4 font-medium">{key.name}</td>
                  <td className="py-3 pr-4">
                    <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">
                      {key.prefix}...
                    </code>
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map((scope) => (
                        <span
                          key={scope}
                          className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-gray-500">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 pr-4 text-gray-500">
                    {key.expires_at
                      ? new Date(key.expires_at).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td className="py-3 pr-4 text-gray-500">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : "Never"}
                  </td>
                  {isAdminOrOwner && (
                    <td className="py-3">
                      {confirmRevoke === key.id ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleRevoke(key.id)}
                            className="text-xs text-red-600 hover:text-red-800 font-medium"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => setConfirmRevoke(null)}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmRevoke(key.id)}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
