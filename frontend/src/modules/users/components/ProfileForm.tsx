"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useCurrentUser, useUpdateProfile } from "../hooks";

const profileSchema = z.object({
  name: z.string().min(1, "Name is required").max(120),
  avatar_url: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export function ProfileForm() {
  const { data: user, isLoading } = useCurrentUser();
  const updateProfile = useUpdateProfile();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: user
      ? { name: user.name, avatar_url: user.avatar_url ?? "" }
      : undefined,
  });

  const onSubmit = async (values: ProfileFormValues) => {
    try {
      await updateProfile.mutateAsync({
        name: values.name,
        avatar_url: values.avatar_url || null,
      });
      toast.success("Profile updated successfully");
    } catch {
      toast.error("Failed to update profile");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-200 rounded w-full" />
        <div className="h-10 bg-gray-200 rounded w-full" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          value={user?.email ?? ""}
          disabled
          className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-500"
        />
        <p className="mt-1 text-xs text-gray-400">
          Email cannot be changed here.
        </p>
      </div>

      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Display Name
        </label>
        <input
          id="name"
          type="text"
          {...register("name")}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
        {errors.name && (
          <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="avatar_url"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Avatar URL
        </label>
        <input
          id="avatar_url"
          type="text"
          {...register("avatar_url")}
          placeholder="https://example.com/avatar.png"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
        {errors.avatar_url && (
          <p className="mt-1 text-xs text-red-500">
            {errors.avatar_url.message}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={!isDirty || updateProfile.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {updateProfile.isPending ? "Saving..." : "Save Changes"}
        </button>

        {user && (
          <span className="text-xs text-gray-400">
            Role: <strong className="capitalize">{user.role}</strong>
          </span>
        )}
      </div>
    </form>
  );
}
