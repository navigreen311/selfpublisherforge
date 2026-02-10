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
