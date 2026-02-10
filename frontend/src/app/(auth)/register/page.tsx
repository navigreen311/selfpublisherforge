"use client";

import * as React from "react";
import Link from "next/link";
import { z } from "zod";
import { Eye, EyeOff, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import {
  getPasswordChecks,
  PASSWORD_CHECK_LABELS,
  validatePassword,
  registerSchema,
  validateForm,
} from "@/lib/validation";

/** Extend the shared registerSchema with the name field to avoid duplicating password rules */
const registerPageSchema = registerSchema.innerType().extend({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be at most 100 characters"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type TouchedFields = Record<string, boolean>;

const plans = [
  { id: "free", name: "Free", description: "Get started with basics", price: "$0" },
  { id: "starter", name: "Starter", description: "For individual authors", price: "$19/mo" },
  { id: "pro", name: "Pro", description: "For professional publishers", price: "$49/mo" },
  { id: "business", name: "Business", description: "For publishing teams", price: "$99/mo" },
];

export default function RegisterPage() {
  const { register, loginWithGoogle, loginWithGitHub, isLoading } = useAuth();
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [orgName, setOrgName] = React.useState("");
  const [plan, setPlan] = React.useState("free");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState("");
  const [touched, setTouched] = React.useState<TouchedFields>({});
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});

  const passwordChecks = getPasswordChecks(password);
  const isPasswordValid = validatePassword(password).valid;

  // Run validation whenever form values change
  React.useEffect(() => {
    const result = validateForm(registerPageSchema, {
      name,
      email,
      password,
      confirmPassword,
    });
    setFieldErrors(result.errors ?? {});
  }, [name, email, password, confirmPassword]);

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  /** Return the error message for a field only if the field has been touched */
  const getFieldError = (field: string): string | undefined => {
    return touched[field] ? fieldErrors[field] : undefined;
  };

  const hasFormErrors = Object.keys(fieldErrors).length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Mark all fields as touched on submit so errors become visible
    setTouched({
      name: true,
      email: true,
      password: true,
      confirmPassword: true,
    });

    if (hasFormErrors) {
      setError("Please fix the errors above before submitting");
      return;
    }

    try {
      await register({ name, email, password, orgName, planTier: plan });
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Registration failed. Please try again."
      );
    }
  };

  const nameError = getFieldError("name");
  const emailError = getFieldError("email");
  const passwordError = getFieldError("password");
  const confirmPasswordError = getFieldError("confirmPassword");

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Create your account</CardTitle>
        <CardDescription>Start your self-publishing journey today</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit} noValidate>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Input
            label="Full Name"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => handleBlur("name")}
            required
            autoComplete="name"
            error={nameError}
          />

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => handleBlur("email")}
            required
            autoComplete="email"
            error={emailError}
          />

          <div className="space-y-1.5">
            <label htmlFor="register-password" className="text-sm font-medium">
              Password
            </label>
            <div className="relative">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => handleBlur("password")}
                required
                autoComplete="new-password"
                aria-invalid={!!passwordError}
                aria-describedby={
                  passwordError
                    ? "register-password-error"
                    : "register-password-checks"
                }
                className={cn(
                  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pr-10",
                  passwordError &&
                    "border-destructive focus-visible:ring-destructive"
                )}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {passwordError && (
              <p
                id="register-password-error"
                className="text-sm text-destructive"
              >
                {passwordError}
              </p>
            )}
            {password && (
              <div
                id="register-password-checks"
                className="grid grid-cols-2 gap-1 mt-2"
              >
                {PASSWORD_CHECK_LABELS.map(({ key, label }) => (
                  <div
                    key={key}
                    className={cn(
                      "flex items-center gap-1 text-xs",
                      passwordChecks[key as keyof typeof passwordChecks]
                        ? "text-green-600"
                        : "text-muted-foreground"
                    )}
                  >
                    <Check className="h-3 w-3" />
                    {label}
                  </div>
                ))}
              </div>
            )}
          </div>

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            onBlur={() => handleBlur("confirmPassword")}
            required
            autoComplete="new-password"
            error={confirmPasswordError}
          />

          <Input
            label="Organization Name"
            placeholder="My Publishing House (optional)"
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
            helperText="You can change this later"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Plan</label>
            <Select value={plan} onValueChange={setPlan}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {plans.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    <span className="flex items-center gap-2">
                      <span className="font-medium">{p.name}</span>
                      <span className="text-muted-foreground">
                        - {p.price}
                      </span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Create account"}
          </Button>

          <div className="relative w-full">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 w-full">
            <Button
              type="button"
              variant="outline"
              onClick={loginWithGoogle}
              disabled={isLoading}
              className="w-full"
            >
              <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Google
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={loginWithGitHub}
              disabled={isLoading}
              className="w-full"
            >
              <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              GitHub
            </Button>
          </div>

          <p className="text-sm text-muted-foreground text-center">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
