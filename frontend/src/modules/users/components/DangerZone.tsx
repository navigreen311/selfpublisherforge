"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useDeleteAccount } from "../hooks";
import { useAuthStore } from "@/lib/store";
import { toast } from "sonner";
import { AlertTriangle } from "lucide-react";

export function DangerZone() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const deleteAccount = useDeleteAccount();
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);

  const handleFirstConfirm = () => {
    setIsDialogOpen(false);
    setIsConfirmDialogOpen(true);
  };

  const handleFinalDelete = async () => {
    if (!password.trim()) {
      toast.error("Please enter your password");
      return;
    }

    if (confirmText !== "DELETE") {
      toast.error('Please type "DELETE" to confirm');
      return;
    }

    try {
      await deleteAccount.mutateAsync(password);
      toast.success("Account deleted successfully");
      logout();
      router.push("/login");
    } catch (error) {
      if (
        typeof error === "object" &&
        error !== null &&
        "response" in error &&
        typeof (error as { response: unknown }).response === "object"
      ) {
        const resp = (error as { response: { data?: { detail?: string } } })
          .response;
        toast.error(resp.data?.detail || "Failed to delete account");
      } else {
        toast.error("Failed to delete account. Please try again.");
      }
    }
  };

  const handleCancel = () => {
    setIsDialogOpen(false);
    setIsConfirmDialogOpen(false);
    setPassword("");
    setConfirmText("");
  };

  return (
    <>
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Danger Zone
          </CardTitle>
          <CardDescription>
            Irreversible and destructive actions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Delete Account</h4>
            <p className="text-sm text-muted-foreground">
              Once you delete your account, there is no going back. All your data,
              including projects, books, and content will be permanently deleted.
            </p>
          </div>

          <Button
            variant="destructive"
            onClick={() => setIsDialogOpen(true)}
          >
            Delete Account
          </Button>
        </CardContent>
      </Card>

      {/* First Confirmation Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you absolutely sure?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete your
              account and remove all your data from our servers.
            </DialogDescription>
          </DialogHeader>

          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Warning:</strong> All of your projects, books, campaigns,
              generated content, and account data will be permanently deleted.
            </AlertDescription>
          </Alert>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleFirstConfirm}>
              Yes, I want to delete my account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Final Confirmation Dialog */}
      <Dialog open={isConfirmDialogOpen} onOpenChange={setIsConfirmDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Final Confirmation Required</DialogTitle>
            <DialogDescription>
              To confirm deletion, please enter your password and type DELETE below.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />

            <div>
              <label
                htmlFor="confirm-delete"
                className="block text-sm font-medium mb-1.5"
              >
                Type <code className="font-mono font-bold">DELETE</code> to confirm
              </label>
              <Input
                id="confirm-delete"
                type="text"
                placeholder="DELETE"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
              />
            </div>

            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                This is your last chance. Once you click &quot;Delete My Account&quot;,
                all your data will be permanently erased and cannot be recovered.
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleFinalDelete}
              disabled={
                !password.trim() ||
                confirmText !== "DELETE" ||
                deleteAccount.isPending
              }
            >
              {deleteAccount.isPending
                ? "Deleting..."
                : "Delete My Account"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
