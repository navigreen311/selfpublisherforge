"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  useCurrentUser,
  useOrg,
  useUpdateOrg,
} from "@/modules/users/hooks";
import { MemberList } from "@/modules/users/components/MemberList";
import { InviteModal } from "@/modules/users/components/InviteModal";

const orgSchema = z.object({
  name: z.string().min(1).max(200),
  slug: z
    .string()
    .min(1)
    .max(100)
    .regex(/^[a-z0-9-]+$/, "Only lowercase letters, numbers, and hyphens"),
});

type OrgFormValues = z.infer<typeof orgSchema>;

export default function OrganizationSettingsPage() {
  const { data: currentUser } = useCurrentUser();
  const orgId = currentUser?.org_id ?? "";
  const { data: org, isLoading } = useOrg(orgId);
  const updateOrg = useUpdateOrg(orgId);
  const [inviteOpen, setInviteOpen] = useState(false);

  const isAdminOrOwner =
    currentUser?.role === "owner" || currentUser?.role === "admin";

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<OrgFormValues>({
    resolver: zodResolver(orgSchema),
    values: org ? { name: org.name, slug: org.slug } : undefined,
  });

  const onSubmit = async (values: OrgFormValues) => {
    try {
      await updateOrg.mutateAsync(values);
      toast.success("Organization updated");
    } catch {
      toast.error("Failed to update organization");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-200 rounded w-1/2" />
        <div className="h-40 bg-gray-100 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Org Details */}
      <div>
        <h2 className="text-lg font-semibold">Organization</h2>
        <p className="text-sm text-gray-500">
          Manage your organization settings and team.
        </p>
      </div>

      {isAdminOrOwner && (
        <div className="rounded-lg border bg-white p-6">
          <h3 className="text-sm font-semibold mb-4">General Settings</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Organization Name
              </label>
              <input
                {...register("name")}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.name.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Slug
              </label>
              <input
                {...register("slug")}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              {errors.slug && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.slug.message}
                </p>
              )}
            </div>

            {org && (
              <p className="text-xs text-gray-400">
                Plan: <strong className="capitalize">{org.plan_tier}</strong>
                {" | "}Max members: {org.max_members}
              </p>
            )}

            <button
              type="submit"
              disabled={!isDirty || updateOrg.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateOrg.isPending ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </div>
      )}

      {/* Team Members */}
      <div className="rounded-lg border bg-white p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Team Members</h3>
          {isAdminOrOwner && (
            <button
              onClick={() => setInviteOpen(true)}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
            >
              Invite Member
            </button>
          )}
        </div>
        {orgId && <MemberList orgId={orgId} />}
      </div>

      {/* Invite Modal */}
      {orgId && (
        <InviteModal
          orgId={orgId}
          open={inviteOpen}
          onClose={() => setInviteOpen(false)}
        />
      )}
    </div>
  );
}
