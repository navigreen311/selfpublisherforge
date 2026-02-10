import { z } from "zod";

// ---------------------------------------------------------------------------
// Zod Schemas
// ---------------------------------------------------------------------------

/** Login form: email + password (min 1 char so the field is not empty) */
export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});
export type LoginFormData = z.infer<typeof loginSchema>;

/** Register form: strong password + confirmation must match */
export const registerSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(8, "Must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain an uppercase letter")
      .regex(/[a-z]/, "Must contain a lowercase letter")
      .regex(/\d/, "Must contain a number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type RegisterFormData = z.infer<typeof registerSchema>;

/** Project form */
export const projectSchema = z.object({
  title: z
    .string()
    .min(2, "Title must be at least 2 characters")
    .max(200, "Title must be at most 200 characters"),
  type: z.enum(["book", "series", "course"], {
    errorMap: () => ({ message: "Type must be book, series, or course" }),
  }),
  genre: z.string().optional(),
  description: z
    .string()
    .max(2000, "Description must be at most 2000 characters")
    .optional()
    .or(z.literal("")),
});
export type ProjectFormData = z.infer<typeof projectSchema>;

/** Publishing metadata */
export const publishingMetadataSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z
    .string()
    .max(4000, "Description must be at most 4000 characters")
    .optional()
    .or(z.literal("")),
  keywords: z
    .array(z.string())
    .max(7, "Maximum of 7 keywords allowed")
    .default([]),
  categories: z
    .array(z.string())
    .max(2, "Maximum of 2 categories allowed")
    .default([]),
  language: z.string().min(1, "Language is required"),
  isbn: z
    .string()
    .regex(
      /^(?:\d{10}|\d{13}|(?:\d{3}-?)?\d{1,5}-?\d{1,7}-?\d{1,7}-?\d)$/,
      "Invalid ISBN format",
    )
    .optional()
    .or(z.literal("")),
});
export type PublishingMetadataFormData = z.infer<typeof publishingMetadataSchema>;

/** Campaign form */
export const campaignSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be at most 100 characters"),
  budget: z.number().positive("Budget must be a positive number"),
  start_date: z.string().min(1, "Start date is required"),
  platform: z.enum(["amazon", "facebook", "google", "bookbub", "other"], {
    errorMap: () => ({ message: "Invalid platform" }),
  }),
});
export type CampaignFormData = z.infer<typeof campaignSchema>;

/** Profile form */
export const profileSchema = z.object({
  display_name: z
    .string()
    .min(2, "Display name must be at least 2 characters")
    .max(50, "Display name must be at most 50 characters"),
  email: z.string().email("Invalid email address"),
});
export type ProfileFormData = z.infer<typeof profileSchema>;

// ---------------------------------------------------------------------------
// Generic form validation helper
// ---------------------------------------------------------------------------

/**
 * Validate arbitrary data against a Zod schema.
 *
 * Returns `{ success: true, data }` on success, or
 * `{ success: false, errors }` with a flat field-name -> message map on failure.
 */
export function validateForm<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
): { success: boolean; data?: T; errors?: Record<string, string> } {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  const errors: Record<string, string> = {};
  for (const issue of result.error.issues) {
    const key = issue.path.join(".");
    // Keep only the first error per field
    if (!errors[key]) {
      errors[key] = issue.message;
    }
  }

  return { success: false, errors };
}

// ---------------------------------------------------------------------------
// Existing validation helpers (kept as-is)
// ---------------------------------------------------------------------------

export const PASSWORD_RULES = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
} as const;

export function validatePassword(password: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (password.length < PASSWORD_RULES.minLength) {
    errors.push(`Must be at least ${PASSWORD_RULES.minLength} characters`);
  }
  if (PASSWORD_RULES.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Must contain an uppercase letter');
  }
  if (PASSWORD_RULES.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Must contain a lowercase letter');
  }
  if (PASSWORD_RULES.requireNumber && !/\d/.test(password)) {
    errors.push('Must contain a number');
  }
  return { valid: errors.length === 0, errors };
}

export function getPasswordStrength(password: string): 'weak' | 'fair' | 'strong' {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 2) return 'weak';
  if (score <= 3) return 'fair';
  return 'strong';
}

export function getPasswordChecks(password: string) {
  return {
    minLength: password.length >= PASSWORD_RULES.minLength,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  };
}

export const PASSWORD_CHECK_LABELS: { key: keyof ReturnType<typeof getPasswordChecks>; label: string }[] = [
  { key: "minLength", label: "8+ characters" },
  { key: "hasUppercase", label: "Uppercase letter" },
  { key: "hasLowercase", label: "Lowercase letter" },
  { key: "hasNumber", label: "Number" },
];
