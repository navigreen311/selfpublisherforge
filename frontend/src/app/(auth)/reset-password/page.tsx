"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Eye, EyeOff, Check } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { getPasswordChecks, PASSWORD_CHECK_LABELS, validatePassword } from "@/lib/validation";

function ResetPasswordForm() {
  const t = useTranslations("auth.resetPassword");
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState(false);

  const passwordChecks = getPasswordChecks(password);
  const isPasswordValid = validatePassword(password).valid;
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!isPasswordValid) {
      setError(t("validation.passwordRequirements"));
      return;
    }

    if (!passwordsMatch) {
      setError(t("validation.passwordsMismatch"));
      return;
    }

    if (!token) {
      setError(t("validation.invalidToken"));
      return;
    }

    setLoading(true);
    try {
      await api.post("/api/v1/auth/reset-password", {
        token,
        new_password: password,
      });
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(t("validation.resetFailed"));
      }
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">{t("invalidLink.title")}</CardTitle>
          <CardDescription>
            {t("invalidLink.description")}
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex flex-col gap-4">
          <Button asChild className="w-full">
            <Link href="/forgot-password">{t("invalidLink.requestButton")}</Link>
          </Button>
          <p className="text-sm text-muted-foreground text-center">
            {t("rememberPassword")}{" "}
            <Link href="/login" className="text-primary hover:underline">
              {t("signIn")}
            </Link>
          </p>
        </CardFooter>
      </Card>
    );
  }

  if (success) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">{t("success.title")}</CardTitle>
          <CardDescription>
            {t("success.description")}
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex flex-col gap-4">
          <Button asChild className="w-full">
            <Link href="/login">{t("success.signInButton")}</Link>
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t("passwordLabel")}</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder={t("passwordPlaceholder")}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {password && (
              <div className="grid grid-cols-2 gap-1 mt-2">
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

          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t("confirmLabel")}</label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                placeholder={t("confirmPlaceholder")}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
                className={cn(
                  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pr-10",
                  confirmPassword && !passwordsMatch && "border-destructive focus-visible:ring-destructive"
                )}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? t("hidePassword") : t("showPassword")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {confirmPassword && !passwordsMatch && (
              <p className="text-sm text-destructive">{t("validation.passwordsMismatch")}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            disabled={loading || !isPasswordValid || !passwordsMatch}
          >
            {loading ? t("submitting") : t("submitButton")}
          </Button>
          <p className="text-sm text-muted-foreground text-center">
            {t("rememberPassword")}{" "}
            <Link href="/login" className="text-primary hover:underline">
              {t("signIn")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  const t = useTranslations("auth.resetPassword");

  return (
    <React.Suspense
      fallback={
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">{t("title")}</CardTitle>
            <CardDescription>{t("loading")}</CardDescription>
          </CardHeader>
        </Card>
      }
    >
      <ResetPasswordForm />
    </React.Suspense>
  );
}
