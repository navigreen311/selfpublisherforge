"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  useChangePassword,
  useEnable2FA,
  useDisable2FA,
  useSessions,
  useRevokeSession,
  useRevokeAllSessions,
  useLoginHistory,
} from "../hooks";

export function SecurityTab() {
  // Change Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  // 2FA state
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [twoFAError, setTwoFAError] = useState("");
  const [twoFASuccess, setTwoFASuccess] = useState("");

  // Hooks
  const changePassword = useChangePassword();
  const enable2FA = useEnable2FA();
  const disable2FA = useDisable2FA();
  const { data: sessions = [] } = useSessions();
  const revokeSession = useRevokeSession();
  const revokeAllSessions = useRevokeAllSessions();
  const { data: loginHistory = [] } = useLoginHistory();

  // Mock 2FA status (in real app, this would come from user data)
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);
  const [mockSecret, setMockSecret] = useState("");

  const handleChangePassword = async () => {
    setPasswordError("");
    setPasswordSuccess("");

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("All fields are required");
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match");
      return;
    }

    try {
      await changePassword.mutateAsync({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess("Password updated successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error: any) {
      setPasswordError(error.message || "Failed to update password");
    }
  };

  const handleEnable2FA = async () => {
    setTwoFAError("");
    setTwoFASuccess("");

    try {
      const result = await enable2FA.mutateAsync();
      // Mock secret for display
      setMockSecret(result?.secret || "JBSWY3DPEHPK3PXP");
      setShow2FASetup(true);
      setIs2FAEnabled(true);
      setTwoFASuccess("2FA enabled successfully");
    } catch (error: any) {
      setTwoFAError(error.message || "Failed to enable 2FA");
    }
  };

  const handleDisable2FA = async () => {
    setTwoFAError("");
    setTwoFASuccess("");

    try {
      await disable2FA.mutateAsync();
      setIs2FAEnabled(false);
      setShow2FASetup(false);
      setTwoFASuccess("2FA disabled successfully");
    } catch (error: any) {
      setTwoFAError(error.message || "Failed to disable 2FA");
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await revokeSession.mutateAsync(sessionId);
    } catch (error: any) {
      console.error("Failed to revoke session:", error);
    }
  };

  const handleRevokeAllSessions = async () => {
    try {
      await revokeAllSessions.mutateAsync();
    } catch (error: any) {
      console.error("Failed to revoke all sessions:", error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Section 1: Change Password */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Current Password</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="new-password">New Password</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          {passwordError && (
            <p className="text-sm text-red-600">{passwordError}</p>
          )}
          {passwordSuccess && (
            <p className="text-sm text-green-600">{passwordSuccess}</p>
          )}

          <Button
            onClick={handleChangePassword}
            disabled={changePassword.isPending}
          >
            {changePassword.isPending ? "Updating..." : "Update Password"}
          </Button>
        </CardContent>
      </Card>

      {/* Section 2: Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Status:</span>
            {is2FAEnabled ? (
              <span className="text-sm text-green-600">✅ Enabled</span>
            ) : (
              <span className="text-sm text-red-600">❌ Not enabled</span>
            )}
          </div>

          <p className="text-sm text-gray-600">
            Two-factor authentication adds an extra layer of security to your
            account by requiring a verification code in addition to your
            password when signing in.
          </p>

          {show2FASetup && is2FAEnabled && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex flex-col items-center gap-4">
                <div className="w-48 h-48 bg-white border-2 border-gray-300 rounded-lg flex items-center justify-center">
                  <span className="text-gray-400 text-sm text-center px-4">
                    QR Code Placeholder
                    <br />
                    Scan with authenticator app
                  </span>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium mb-1">
                    Or enter this code manually:
                  </p>
                  <code className="text-sm bg-white px-3 py-1 rounded border">
                    {mockSecret}
                  </code>
                </div>
              </div>
            </div>
          )}

          {twoFAError && (
            <p className="text-sm text-red-600">{twoFAError}</p>
          )}
          {twoFASuccess && (
            <p className="text-sm text-green-600">{twoFASuccess}</p>
          )}

          {is2FAEnabled ? (
            <Button
              variant="destructive"
              onClick={handleDisable2FA}
              disabled={disable2FA.isPending}
            >
              {disable2FA.isPending ? "Disabling..." : "Disable 2FA"}
            </Button>
          ) : (
            <Button
              onClick={handleEnable2FA}
              disabled={enable2FA.isPending}
            >
              {enable2FA.isPending ? "Enabling..." : "Enable 2FA"}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500">No active sessions</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session: any) => (
                <div
                  key={session.id}
                  className="flex items-start justify-between p-4 border rounded-lg"
                >
                  <div className="flex gap-3 flex-1">
                    <div className="text-2xl">
                      {session.device === "mobile" ? "📱" : "🖥️"}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">
                          {session.browser} on {session.os}
                        </span>
                        {session.isCurrent && (
                          <Badge variant="secondary" className="text-xs">
                            Current session
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        {session.location}
                      </p>
                      <p className="text-xs text-gray-500">
                        IP: {session.ipAddress} • Last active:{" "}
                        {session.lastActive}
                      </p>
                    </div>
                  </div>
                  {!session.isCurrent && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRevokeSession(session.id)}
                      disabled={revokeSession.isPending}
                    >
                      Revoke
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}

          {sessions.filter((s: any) => !s.isCurrent).length > 0 && (
            <>
              <Separator />
              <Button
                variant="outline"
                onClick={handleRevokeAllSessions}
                disabled={revokeAllSessions.isPending}
              >
                {revokeAllSessions.isPending
                  ? "Revoking..."
                  : "Revoke All Other Sessions"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Section 4: Login History */}
      <Card>
        <CardHeader>
          <CardTitle>Login History</CardTitle>
        </CardHeader>
        <CardContent>
          {loginHistory.length === 0 ? (
            <p className="text-sm text-gray-500">No login history available</p>
          ) : (
            <div className="space-y-3">
              {loginHistory.slice(0, 10).map((entry: any, index: number) => (
                <div
                  key={index}
                  className="flex items-start justify-between p-3 border-b last:border-0"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {entry.timestamp}
                      </span>
                      {entry.success ? (
                        <span className="text-green-600 text-sm">✅ Success</span>
                      ) : (
                        <span className="text-red-600 text-sm">❌ Failed</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      {entry.browser} on {entry.os}
                    </p>
                    <p className="text-xs text-gray-500">{entry.location}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
