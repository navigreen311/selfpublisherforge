"use client";

import { useState, useCallback, useEffect } from "react";
import { useCurrentUser } from "@/modules/users/hooks";
import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useQueryClient } from "@tanstack/react-query";
import { userKeys } from "@/modules/users/hooks";
import { useTranslations } from "@/hooks/use-translations";

// ─── Types ──────────────────────────────────────────────────────────────────

interface MFASetupResponse {
  secret: string;
  qr_code_url: string;
  backup_codes: string[];
}

// ─── Backup Codes Display ───────────────────────────────────────────────────

function BackupCodesDisplay({ codes }: { codes: string[] }) {
  const t = useTranslations("settings.security.mfa");
  const [copied, setCopied] = useState(false);

  const handleCopyAll = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(codes.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for environments where clipboard API is unavailable
      const textArea = document.createElement("textarea");
      textArea.value = codes.join("\n");
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [codes]);

  const handleDownload = useCallback(() => {
    const content = [
      "SelfPublisherForge - MFA Backup Codes",
      "======================================",
      "",
      "Store these codes in a safe place. Each code can only be used once.",
      "",
      ...codes.map((code, i) => `${i + 1}. ${code}`),
      "",
      `Generated: ${new Date().toISOString()}`,
    ].join("\n");

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "selfpublisherforge-backup-codes.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [codes]);

  return (
    <div className="space-y-3">
      <Alert>
        <AlertTitle>{t("backupCodesTitle")}</AlertTitle>
        <AlertDescription>
          {t("backupCodesDescription")}
        </AlertDescription>
      </Alert>

      <div
        className="grid grid-cols-2 gap-2 rounded-md border bg-muted/50 p-4"
        role="list"
        aria-label="Backup codes"
      >
        {codes.map((code) => (
          <code
            key={code}
            role="listitem"
            className="rounded bg-background px-2 py-1 text-center text-sm font-mono"
          >
            {code}
          </code>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleCopyAll} aria-label="Copy all backup codes to clipboard">
          {copied ? t("copied") : t("copyAll")}
        </Button>
        <Button variant="outline" size="sm" onClick={handleDownload} aria-label="Download backup codes as text file">
          {t("downloadTxt")}
        </Button>
      </div>
    </div>
  );
}

// ─── MFA Setup Flow ─────────────────────────────────────────────────────────

function MFASetupFlow({
  onComplete,
  onCancel,
}: {
  onComplete: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations("settings.security.mfa");
  const tCommon = useTranslations("common");
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"loading" | "display" | "verified">(
    "loading"
  );

  // Initiate MFA setup on mount
  const initSetup = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<MFASetupResponse>(
        "/api/v1/auth/mfa/setup"
      );
      setSetupData(data);
      setStep("display");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : t("setupFailed");
      // Check for axios error response
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as Record<string, unknown>).response === "object"
      ) {
        const resp = (err as { response: { data?: { detail?: string } } })
          .response;
        setError(resp.data?.detail || message);
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [t]);

  // Call setup on first render
  useEffect(() => {
    initSetup();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleVerify = async () => {
    if (verifyCode.length !== 6) {
      setError("Please enter a 6-digit code.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/auth/mfa/verify", { code: verifyCode });
      setStep("verified");
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as Record<string, unknown>).response === "object"
      ) {
        const resp = (err as { response: { data?: { detail?: string } } })
          .response;
        setError(resp.data?.detail || "Verification failed. Please try again.");
      } else {
        setError("Verification failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (step === "loading" && !setupData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {t("settingUp")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status" aria-live="polite">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" aria-hidden="true" />
              {t("generatingSecret")}
            </div>
          ) : error ? (
            <div className="space-y-3">
              <Alert variant="destructive">
                <AlertTitle>{t("setupFailed")}</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onCancel}>
                  {tCommon("cancel")}
                </Button>
                <Button onClick={initSetup}>Try Again</Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    );
  }

  if (step === "verified") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {t("enabledTitle")}
          </CardTitle>
          <CardDescription>
            {t("protectedAccount")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {setupData && <BackupCodesDisplay codes={setupData.backup_codes} />}
          <Button onClick={onComplete}>{t("done")}</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          {t("setupTitle")}
        </CardTitle>
        <CardDescription>
          {t("setupDescription")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* QR Code */}
        {setupData && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="rounded-lg border bg-white p-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={setupData.qr_code_url}
                  alt="Scan this QR code with your authenticator app to set up two-factor authentication"
                  width={200}
                  height={200}
                  className="h-[200px] w-[200px]"
                />
              </div>
            </div>

            {/* Manual Secret Key */}
            <div className="space-y-1.5">
              <p id="manual-key-description" className="text-sm font-medium">
                {t("cantScanQr")}
              </p>
              <div className="flex items-center gap-2">
                <code
                  className="flex-1 rounded border bg-muted px-3 py-2 text-sm font-mono select-all"
                  aria-describedby="manual-key-description"
                  role="textbox"
                  aria-readonly="true"
                  aria-label="MFA secret key"
                >
                  {setupData.secret}
                </code>
              </div>
            </div>

            {/* Backup Codes */}
            <BackupCodesDisplay codes={setupData.backup_codes} />
          </div>
        )}

        {/* Verification Input */}
        <fieldset className="space-y-3 border-t pt-4">
          <legend className="sr-only">Verify authenticator setup</legend>
          <label htmlFor="mfa-verify-code" className="text-sm font-medium">
            {t("verifyPrompt")}
          </label>
          <div className="flex gap-2">
            <Input
              id="mfa-verify-code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              placeholder={t("verifyCode")}
              value={verifyCode}
              onChange={(e) =>
                setVerifyCode(e.target.value.replace(/\D/g, "").slice(0, 6))
              }
              className="max-w-[160px] text-center text-lg tracking-widest font-mono"
              aria-required="true"
              aria-describedby={error ? "mfa-verify-error" : undefined}
              aria-invalid={!!error}
            />
            <Button
              onClick={handleVerify}
              disabled={verifyCode.length !== 6 || loading}
            >
              {loading ? t("verifying") : t("verifyAndEnable")}
            </Button>
          </div>
          {error && (
            <p id="mfa-verify-error" className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </fieldset>

        {/* Cancel */}
        <div className="border-t pt-4">
          <Button variant="ghost" onClick={onCancel}>
            {t("cancelSetup")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Disable MFA Dialog ─────────────────────────────────────────────────────

function DisableMFADialog({
  open,
  onOpenChange,
  onDisabled,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDisabled: () => void;
}) {
  const t = useTranslations("settings.security.mfa");
  const tCommon = useTranslations("common");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDisable = async () => {
    if (!password.trim()) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/auth/mfa/disable", { password });
      setPassword("");
      onOpenChange(false);
      onDisabled();
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as Record<string, unknown>).response === "object"
      ) {
        const resp = (err as { response: { data?: { detail?: string } } })
          .response;
        setError(resp.data?.detail || "Failed to disable MFA.");
      } else {
        setError("Failed to disable MFA. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("disableTitle")}</DialogTitle>
          <DialogDescription>
            {t("disableDescription")}
          </DialogDescription>
        </DialogHeader>

        <fieldset className="space-y-3 py-2">
          <legend className="sr-only">Confirm MFA disable</legend>
          <Input
            id="disable-mfa-password"
            type="password"
            label={tCommon("password")}
            placeholder={t("enterPassword")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={error ?? undefined}
            aria-required="true"
            autoFocus
          />
        </fieldset>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              setPassword("");
              setError(null);
              onOpenChange(false);
            }}
          >
            {tCommon("cancel")}
          </Button>
          <Button
            variant="destructive"
            onClick={handleDisable}
            disabled={!password.trim() || loading}
          >
            {loading ? t("disabling") : t("disableMfa")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─── Main Security Page ─────────────────────────────────────────────────────

export default function SecuritySettingsPage() {
  const tMfa = useTranslations("settings.security.mfa");
  const tSecurity = useTranslations("settings.security");
  const { data: currentUser, isLoading } = useCurrentUser();
  const queryClient = useQueryClient();

  const [setupMode, setSetupMode] = useState(false);
  const [disableDialogOpen, setDisableDialogOpen] = useState(false);

  const mfaEnabled = currentUser?.mfa_enabled ?? false;

  const handleSetupComplete = () => {
    setSetupMode(false);
    // Refresh user data to reflect the new MFA status
    queryClient.invalidateQueries({ queryKey: userKeys.me });
  };

  const handleMFADisabled = () => {
    // Refresh user data to reflect the new MFA status
    queryClient.invalidateQueries({ queryKey: userKeys.me });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4" aria-busy="true" aria-label={tSecurity("loadingSettings")}>
        <div className="h-10 bg-gray-200 rounded w-1/3" />
        <div className="h-40 bg-gray-100 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 id="security-settings-heading" className="text-lg font-semibold">{tSecurity("heading")}</h2>
        <p className="text-sm text-gray-500">
          {tSecurity("description")}
        </p>
      </div>

      {/* MFA Setup Flow */}
      {setupMode && !mfaEnabled ? (
        <MFASetupFlow
          onComplete={handleSetupComplete}
          onCancel={() => setSetupMode(false)}
        />
      ) : mfaEnabled ? (
        /* MFA Enabled State */
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {tMfa("title")}
            </CardTitle>
            <CardDescription>
              {tMfa("enabledDescription")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-md border border-green-200 bg-green-50 p-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100">
                <svg
                  className="h-5 w-5 text-green-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-green-800">
                  {tMfa("enabled")}
                </p>
                <p className="text-sm text-green-700">
                  {tMfa("enabledPrompt")}
                </p>
              </div>
            </div>

            <Button
              variant="destructive"
              onClick={() => setDisableDialogOpen(true)}
            >
              {tMfa("disableButton")}
            </Button>
          </CardContent>
        </Card>
      ) : (
        /* MFA Not Enabled State */
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {tMfa("title")}
            </CardTitle>
            <CardDescription>
              {tMfa("description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>{tMfa("benefits.title")}</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>
                  {tMfa("benefits.requireCode")}
                </li>
                <li>
                  {tMfa("benefits.preventUnauthorized")}
                </li>
                <li>
                  {tMfa("benefits.backupCodes")}
                </li>
              </ul>
            </div>
            <Button onClick={() => setSetupMode(true)}>
              {tMfa("enableButton")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Disable MFA Confirmation Dialog */}
      <DisableMFADialog
        open={disableDialogOpen}
        onOpenChange={setDisableDialogOpen}
        onDisabled={handleMFADisabled}
      />
    </div>
  );
}
