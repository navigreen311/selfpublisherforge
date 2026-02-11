"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useCurrentUser, useUpdateProfile } from "../hooks";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AvatarUpload } from "./AvatarUpload";
import { Trash2, Plus } from "lucide-react";

// ─── Schema ─────────────────────────────────────────────────────────────────

const profileSchema = z.object({
  name: z.string().min(1, "Name is required").max(120),
  bio: z.string().max(500, "Bio must be 500 characters or less").optional(),
  avatar_url: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
  timezone: z.string().min(1, "Timezone is required"),
  language: z.string().min(1, "Language is required"),
  pen_names: z.array(
    z.object({
      name: z.string().min(1, "Pen name cannot be empty").max(100),
    })
  ),
  social_links: z.object({
    website: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
    twitter: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
    amazon_author_page: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
  }),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

// ─── Timezone Options ───────────────────────────────────────────────────────

const TIMEZONES = [
  { value: "UTC", label: "UTC (Coordinated Universal Time)" },
  { value: "America/New_York", label: "Eastern Time (US & Canada)" },
  { value: "America/Chicago", label: "Central Time (US & Canada)" },
  { value: "America/Denver", label: "Mountain Time (US & Canada)" },
  { value: "America/Los_Angeles", label: "Pacific Time (US & Canada)" },
  { value: "Europe/London", label: "London" },
  { value: "Europe/Paris", label: "Paris" },
  { value: "Europe/Berlin", label: "Berlin" },
  { value: "Asia/Tokyo", label: "Tokyo" },
  { value: "Asia/Shanghai", label: "Shanghai" },
  { value: "Australia/Sydney", label: "Sydney" },
];

// ─── Language Options ───────────────────────────────────────────────────────

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "it", label: "Italian" },
  { value: "pt", label: "Portuguese" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
];

// ─── Component ──────────────────────────────────────────────────────────────

export function ProfileForm() {
  const { data: user, isLoading } = useCurrentUser();
  const updateProfile = useUpdateProfile();

  // Extract preferences from user data
  const userPreferences = (user?.preferences || {}) as {
    bio?: string;
    timezone?: string;
    language?: string;
    pen_names?: Array<{ name: string }>;
    social_links?: {
      website?: string;
      twitter?: string;
      amazon_author_page?: string;
    };
  };

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: user
      ? {
          name: user.name,
          bio: userPreferences.bio ?? "",
          avatar_url: user.avatar_url ?? "",
          timezone: userPreferences.timezone ?? "UTC",
          language: userPreferences.language ?? "en",
          pen_names: userPreferences.pen_names ?? [],
          social_links: {
            website: userPreferences.social_links?.website ?? "",
            twitter: userPreferences.social_links?.twitter ?? "",
            amazon_author_page:
              userPreferences.social_links?.amazon_author_page ?? "",
          },
        }
      : undefined,
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "pen_names",
  });

  const onSubmit = async (values: ProfileFormValues) => {
    try {
      // Merge form values into preferences
      const preferences = {
        ...userPreferences,
        bio: values.bio,
        timezone: values.timezone,
        language: values.language,
        pen_names: values.pen_names,
        social_links: values.social_links,
      };

      await updateProfile.mutateAsync({
        name: values.name,
        avatar_url: values.avatar_url || null,
        preferences,
      });
      toast.success("Profile updated successfully");
    } catch {
      toast.error("Failed to update profile");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4" aria-busy="true">
        <div className="h-10 bg-gray-200 rounded w-full" />
        <div className="h-10 bg-gray-200 rounded w-full" />
        <div className="h-20 bg-gray-200 rounded w-full" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Avatar Upload */}
      <div>
        <label className="block text-sm font-medium mb-3">Profile Picture</label>
        <AvatarUpload
          currentUrl={watch("avatar_url") || null}
          onUploadComplete={(url) => setValue("avatar_url", url, { shouldDirty: true })}
        />
      </div>

      {/* Email (read-only) */}
      <Input
        label="Email"
        type="email"
        value={user?.email ?? ""}
        disabled
        helperText="Email cannot be changed here."
      />

      {/* Display Name */}
      <Input
        label="Display Name"
        type="text"
        {...register("name")}
        error={errors.name?.message}
      />

      {/* Bio */}
      <div>
        <label
          htmlFor="bio"
          className="block text-sm font-medium mb-1.5"
        >
          Bio
        </label>
        <Textarea
          id="bio"
          {...register("bio")}
          placeholder="Tell readers about yourself..."
          className="min-h-[100px]"
        />
        {errors.bio && (
          <p className="mt-1.5 text-sm text-destructive">{errors.bio.message}</p>
        )}
      </div>

      {/* Timezone */}
      <div>
        <label htmlFor="timezone" className="block text-sm font-medium mb-1.5">
          Timezone
        </label>
        <Select
          value={watch("timezone")}
          onValueChange={(value) => setValue("timezone", value, { shouldDirty: true })}
        >
          <SelectTrigger id="timezone">
            <SelectValue placeholder="Select timezone" />
          </SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz.value} value={tz.value}>
                {tz.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.timezone && (
          <p className="mt-1.5 text-sm text-destructive">{errors.timezone.message}</p>
        )}
      </div>

      {/* Language */}
      <div>
        <label htmlFor="language" className="block text-sm font-medium mb-1.5">
          Preferred Language
        </label>
        <Select
          value={watch("language")}
          onValueChange={(value) => setValue("language", value, { shouldDirty: true })}
        >
          <SelectTrigger id="language">
            <SelectValue placeholder="Select language" />
          </SelectTrigger>
          <SelectContent>
            {LANGUAGES.map((lang) => (
              <SelectItem key={lang.value} value={lang.value}>
                {lang.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.language && (
          <p className="mt-1.5 text-sm text-destructive">{errors.language.message}</p>
        )}
      </div>

      {/* Pen Names */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium">Pen Names</label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => append({ name: "" })}
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Add Pen Name
          </Button>
        </div>
        {fields.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No pen names added yet. Click &quot;Add Pen Name&quot; to create one.
          </p>
        )}
        <div className="space-y-2">
          {fields.map((field, index) => (
            <div key={field.id} className="flex gap-2">
              <Input
                {...register(`pen_names.${index}.name`)}
                placeholder="Jane Doe"
                error={errors.pen_names?.[index]?.name?.message}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => remove(index)}
                aria-label="Remove pen name"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Social Links */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Social Links</h3>
        <Input
          label="Website"
          type="url"
          {...register("social_links.website")}
          placeholder="https://example.com"
          error={errors.social_links?.website?.message}
        />
        <Input
          label="Twitter/X Profile"
          type="url"
          {...register("social_links.twitter")}
          placeholder="https://twitter.com/username"
          error={errors.social_links?.twitter?.message}
        />
        <Input
          label="Amazon Author Page"
          type="url"
          {...register("social_links.amazon_author_page")}
          placeholder="https://amazon.com/author/username"
          error={errors.social_links?.amazon_author_page?.message}
        />
      </div>

      {/* Submit */}
      <div className="flex items-center gap-3 pt-4 border-t">
        <Button
          type="submit"
          disabled={!isDirty || updateProfile.isPending}
        >
          {updateProfile.isPending ? "Saving..." : "Save Changes"}
        </Button>

        {user && (
          <span className="text-xs text-muted-foreground">
            Role: <strong className="capitalize">{user.role}</strong>
          </span>
        )}
      </div>
    </form>
  );
}
