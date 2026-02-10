import {
  validatePassword,
  getPasswordStrength,
  getPasswordChecks,
  PASSWORD_RULES,
  PASSWORD_CHECK_LABELS,
} from "../validation";

// ─── validatePassword ───────────────────────────────────────────────────────

describe("validatePassword", () => {
  it("returns valid for a password meeting all rules", () => {
    const result = validatePassword("MyPass1word");
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("returns valid for a minimal valid password", () => {
    const result = validatePassword("Abcdefg1");
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("fails when password is too short", () => {
    const result = validatePassword("Ab1cde");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(
      `Must be at least ${PASSWORD_RULES.minLength} characters`
    );
  });

  it("fails when password is missing uppercase letter", () => {
    const result = validatePassword("abcdefg1");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Must contain an uppercase letter");
  });

  it("fails when password is missing lowercase letter", () => {
    const result = validatePassword("ABCDEFG1");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Must contain a lowercase letter");
  });

  it("fails when password is missing a number", () => {
    const result = validatePassword("Abcdefgh");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Must contain a number");
  });

  it("returns all errors for an empty string", () => {
    const result = validatePassword("");
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(4);
    expect(result.errors).toContain(
      `Must be at least ${PASSWORD_RULES.minLength} characters`
    );
    expect(result.errors).toContain("Must contain an uppercase letter");
    expect(result.errors).toContain("Must contain a lowercase letter");
    expect(result.errors).toContain("Must contain a number");
  });

  it("returns multiple errors for a short all-lowercase string", () => {
    const result = validatePassword("abc");
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThanOrEqual(3);
    expect(result.errors).toContain(
      `Must be at least ${PASSWORD_RULES.minLength} characters`
    );
    expect(result.errors).toContain("Must contain an uppercase letter");
    expect(result.errors).toContain("Must contain a number");
  });

  it("passes for a very long valid password", () => {
    const longPassword = "Aa1" + "x".repeat(100);
    const result = validatePassword(longPassword);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("fails for a password of only numbers", () => {
    const result = validatePassword("12345678");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Must contain an uppercase letter");
    expect(result.errors).toContain("Must contain a lowercase letter");
    expect(result.errors).not.toContain("Must contain a number");
  });

  it("fails for a password of only special characters", () => {
    const result = validatePassword("!@#$%^&*");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Must contain an uppercase letter");
    expect(result.errors).toContain("Must contain a lowercase letter");
    expect(result.errors).toContain("Must contain a number");
  });
});

// ─── getPasswordStrength ────────────────────────────────────────────────────

describe("getPasswordStrength", () => {
  it('returns "weak" for an empty string', () => {
    expect(getPasswordStrength("")).toBe("weak");
  });

  it('returns "weak" for a short lowercase-only password', () => {
    expect(getPasswordStrength("abc")).toBe("weak");
  });

  it('returns "weak" for a password that only meets length requirement', () => {
    // Only 1 point: length >= 8
    expect(getPasswordStrength("abcdefgh")).toBe("weak");
  });

  it('returns "fair" for a medium-strength password', () => {
    // Score: length>=8 (1) + mixed case (1) + digit (1) = 3
    expect(getPasswordStrength("Abcdefg1")).toBe("fair");
  });

  it('returns "strong" for a password with all criteria', () => {
    // Score: length>=8 (1) + length>=12 (1) + mixed case (1) + digit (1) + special (1) = 5
    expect(getPasswordStrength("MyStr0ng!Pass")).toBe("strong");
  });

  it('returns "strong" for a very long mixed password', () => {
    const longPassword = "Aa1!xyzXYZ" + "a".repeat(50);
    expect(getPasswordStrength(longPassword)).toBe("strong");
  });

  it('returns "weak" for only special characters below 8 chars', () => {
    expect(getPasswordStrength("!@#$")).toBe("weak");
  });

  it('returns "fair" for 12+ chars lowercase only with a digit', () => {
    // Score: length>=8 (1) + length>=12 (1) + digit (1) = 3
    expect(getPasswordStrength("abcdefghijk1")).toBe("fair");
  });

  it('returns "strong" for 12+ chars with all criteria', () => {
    // Score: length>=8 (1) + length>=12 (1) + mixed case (1) + digit (1) + special (1) = 5
    expect(getPasswordStrength("Abcdefghijk1!")).toBe("strong");
  });

  it("scoring: length>=8 gives 1 point", () => {
    // "aaaaaaaa" = 8 chars, all lowercase => score: 1 (length) => weak
    expect(getPasswordStrength("aaaaaaaa")).toBe("weak");
  });

  it("scoring: length>=12 gives additional point", () => {
    // "aaaaaaaaaaaa" = 12 chars, all lowercase => score: 2 (length8 + length12) => weak
    expect(getPasswordStrength("aaaaaaaaaaaa")).toBe("weak");
  });

  it("scoring: mixed case adds a point", () => {
    // "Aaaaaaaaaaaa" = 12 chars, mixed case => score: 3 => fair
    expect(getPasswordStrength("Aaaaaaaaaaaa")).toBe("fair");
  });
});

// ─── getPasswordChecks ──────────────────────────────────────────────────────

describe("getPasswordChecks", () => {
  it("returns all true for a valid password", () => {
    const checks = getPasswordChecks("MyPassword1");
    expect(checks).toEqual({
      minLength: true,
      hasUppercase: true,
      hasLowercase: true,
      hasNumber: true,
    });
  });

  it("returns all false for an empty string", () => {
    const checks = getPasswordChecks("");
    expect(checks).toEqual({
      minLength: false,
      hasUppercase: false,
      hasLowercase: false,
      hasNumber: false,
    });
  });

  it("correctly identifies missing criteria", () => {
    const checks = getPasswordChecks("abcdef");
    expect(checks.minLength).toBe(false);
    expect(checks.hasUppercase).toBe(false);
    expect(checks.hasLowercase).toBe(true);
    expect(checks.hasNumber).toBe(false);
  });

  it("correctly checks for uppercase-only password", () => {
    const checks = getPasswordChecks("ABCDEFGH");
    expect(checks.minLength).toBe(true);
    expect(checks.hasUppercase).toBe(true);
    expect(checks.hasLowercase).toBe(false);
    expect(checks.hasNumber).toBe(false);
  });

  it("correctly checks for number-only password", () => {
    const checks = getPasswordChecks("12345678");
    expect(checks.minLength).toBe(true);
    expect(checks.hasUppercase).toBe(false);
    expect(checks.hasLowercase).toBe(false);
    expect(checks.hasNumber).toBe(true);
  });
});

// ─── PASSWORD_RULES and PASSWORD_CHECK_LABELS ──────────────────────────────

describe("PASSWORD_RULES", () => {
  it("has a minimum length of 8", () => {
    expect(PASSWORD_RULES.minLength).toBe(8);
  });

  it("requires uppercase letters", () => {
    expect(PASSWORD_RULES.requireUppercase).toBe(true);
  });

  it("requires lowercase letters", () => {
    expect(PASSWORD_RULES.requireLowercase).toBe(true);
  });

  it("requires numbers", () => {
    expect(PASSWORD_RULES.requireNumber).toBe(true);
  });
});

describe("PASSWORD_CHECK_LABELS", () => {
  it("has 4 check labels", () => {
    expect(PASSWORD_CHECK_LABELS).toHaveLength(4);
  });

  it("includes minLength check", () => {
    expect(PASSWORD_CHECK_LABELS.find((c) => c.key === "minLength")).toBeDefined();
  });

  it("includes hasUppercase check", () => {
    expect(PASSWORD_CHECK_LABELS.find((c) => c.key === "hasUppercase")).toBeDefined();
  });

  it("includes hasLowercase check", () => {
    expect(PASSWORD_CHECK_LABELS.find((c) => c.key === "hasLowercase")).toBeDefined();
  });

  it("includes hasNumber check", () => {
    expect(PASSWORD_CHECK_LABELS.find((c) => c.key === "hasNumber")).toBeDefined();
  });
});
