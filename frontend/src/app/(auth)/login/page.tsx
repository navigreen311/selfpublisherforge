import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Login",
  description: "Sign in to your SelfPublisherForge account to manage your books, track royalties, and grow your publishing business.",
});

"use client";

import * as React from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
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
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/hooks/use-auth";
import { useTranslations } from "@/hooks/use-translations";

export default function LoginPage() {
  const t = useTranslations("auth.login");
  const tCommon = useTranslations("common");
  const { login, loginWithGoogle, loginWithGitHub, isLoading } = useAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [mfaCode, setMfaCode] = React.useState("");
  const [showMfa, setShowMfa] = React.useState(false);
  const [rememberMe, setRememberMe] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login({ email, password, mfaCode: showMfa ? mfaCode : undefined, rememberMe });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : t("invalidCredentials");
      if (message.includes("MFA") || message.includes("mfa")) {
        setShowMfa(true);
      } else {
        setError(message);
      }
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto px-4 sm:px-6">
      <CardHeader className="text-center px-4 sm:px-6">
        <CardTitle className="text-xl sm:text-2xl">{t("title")}</CardTitle>
        <CardDescription className="text-sm sm:text-base">{t("description")}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-3 sm:space-y-4 px-4 sm:px-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Input
            label={t("email")}
            type="email"
            placeholder={t("emailPlaceholder")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t("password")}</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder={t("passwordPlaceholder")}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground min-h-[44px] min-w-[44px] flex items-center justify-center"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 sm:h-4 sm:w-4" />
                ) : (
                  <Eye className="h-5 w-5 sm:h-4 sm:w-4" />
                )}
              </button>
            </div>
          </div>

          {showMfa && (
            <Input
              label={t("mfaCode")}
              placeholder={t("mfaCodePlaceholder")}
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              maxLength={6}
              autoComplete="one-time-code"
            />
          )}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <div className="flex items-center gap-2 min-h-[44px]">
              <Switch
                checked={rememberMe}
                onCheckedChange={setRememberMe}
                id="remember"
              />
              <label htmlFor="remember" className="text-sm sm:text-base">
                {t("rememberMe")}
              </label>
            </div>
            <Link
              href="/forgot-password"
              className="text-sm sm:text-base text-primary hover:underline min-h-[44px] flex items-center"
            >
              {t("forgotPassword")}
            </Link>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:gap-4 px-4 sm:px-6">
          <Button type="submit" className="w-full min-h-[44px]" disabled={isLoading}>
            {isLoading ? t("submitting") : t("submit")}
          </Button>

          <div className="relative w-full">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs sm:text-sm uppercase">
              <span className="bg-card px-2 text-muted-foreground">
                {t("orContinueWith")}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:grid sm:grid-cols-2 gap-3 w-full">
            <Button
              type="button"
              variant="outline"
              onClick={loginWithGoogle}
              disabled={isLoading}
              className="w-full min-h-[44px]"
            >
              <svg className="mr-2 h-4 w-4 sm:h-5 sm:w-5" viewBox="0 0 24 24">
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
              {t("google")}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={loginWithGitHub}
              disabled={isLoading}
              className="w-full min-h-[44px]"
            >
              <svg className="mr-2 h-4 w-4 sm:h-5 sm:w-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              {t("github")}
            </Button>
          </div>

          <p className="text-sm sm:text-base text-muted-foreground text-center">
            {t("noAccount")}{" "}
            <Link href="/register" className="text-primary hover:underline min-h-[44px] inline-flex items-center">
              {t("createAccount")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
