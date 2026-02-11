"use client";

import * as React from "react";
import Link from "next/link";
import { Mail } from "lucide-react";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { api } from "@/lib/api";
import { useTranslations } from "@/hooks/use-translations";

export default function ForgotPasswordPage() {
  const t = useTranslations("auth.forgotPassword");
  const [email, setEmail] = React.useState("");
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/v1/auth/forgot-password", { email });
      setSubmitted(true);
    } catch {
      // Always show success to prevent email enumeration
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Card className="w-full max-w-md mx-auto px-4 sm:px-6">
        <CardHeader className="text-center px-4 sm:px-6">
          <div className="mx-auto mb-4 flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
          </div>
          <CardTitle className="text-xl sm:text-2xl">{t("checkEmailTitle")}</CardTitle>
          <CardDescription className="text-sm sm:text-base">
            {t("checkEmailDescription", { email })}
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex flex-col gap-3 sm:gap-4 px-4 sm:px-6">
          <Button asChild variant="outline" className="w-full min-h-[44px]">
            <Link href="/login">{t("backToSignIn")}</Link>
          </Button>
          <p className="text-sm sm:text-base text-muted-foreground text-center">
            {t("didntReceiveEmail")}{" "}
            <button
              type="button"
              onClick={() => setSubmitted(false)}
              className="text-primary hover:underline min-h-[44px] inline-flex items-center"
            >
              {t("tryAgain")}
            </button>
          </p>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto px-4 sm:px-6">
      <CardHeader className="text-center px-4 sm:px-6">
        <CardTitle className="text-xl sm:text-2xl">{t("title")}</CardTitle>
        <CardDescription className="text-sm sm:text-base">
          {t("description")}
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-3 sm:space-y-4 px-4 sm:px-6">
          <Input
            label={t("email")}
            type="email"
            placeholder={t("emailPlaceholder")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:gap-4 px-4 sm:px-6">
          <Button type="submit" className="w-full min-h-[44px]" disabled={loading}>
            {loading ? t("submitting") : t("submit")}
          </Button>
          <p className="text-sm sm:text-base text-muted-foreground text-center">
            {t("rememberPassword")}{" "}
            <Link href="/login" className="text-primary hover:underline min-h-[44px] inline-flex items-center">
              {t("signIn")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
