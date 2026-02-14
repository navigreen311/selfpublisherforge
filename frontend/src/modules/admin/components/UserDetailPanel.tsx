"use client";

import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminUserDetail, useUpdateAdminUser, useDeactivateUser, useResetUserPassword } from "../hooks";
import { useToast } from "@/hooks/use-toast";

interface UserDetailPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
}

const ALL_PERMISSIONS = [
  "writing_studio",
  "cover_design",
  "publishing",
  "marketing",
  "ai_agents",
  "admin_panel",
  "billing",
];

const PERMISSION_LABELS: Record<string, string> = {
  writing_studio: "Writing Studio",
  cover_design: "Cover Design",
  publishing: "Publishing",
  marketing: "Marketing",
  ai_agents: "AI Agents",
  admin_panel: "Admin Panel",
  billing: "Billing",
};

export function UserDetailPanel({ open, onOpenChange, userId }: UserDetailPanelProps) {
  const { data: user, isLoading } = useAdminUserDetail(userId);
  const updateUser = useUpdateAdminUser();
  const deactivateUser = useDeactivateUser();
  const resetPassword = useResetUserPassword();
  const { toast } = useToast();

  const [role, setRole] = useState<string>("");
  const [permissions, setPermissions] = useState<string[]>([]);

  useEffect(() => {
    if (user) {
      setRole(user.role);
      setPermissions(user.permissions || []);
    }
  }, [user]);

  const handleSaveChanges = async () => {
    try {
      await updateUser.mutateAsync({
        userId,
        data: {
          role,
          permissions,
        },
      });
      toast({
        title: "Success",
        description: "User updated successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update user",
        variant: "destructive",
      });
    }
  };

  const handleResetPassword = async () => {
    try {
      await resetPassword.mutateAsync(userId);
      toast({
        title: "Success",
        description: "Password reset email sent",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to reset password",
        variant: "destructive",
      });
    }
  };

  const handleDeactivate = async () => {
    if (!confirm("Are you sure you want to deactivate this user?")) return;

    try {
      await deactivateUser.mutateAsync(userId);
      toast({
        title: "Success",
        description: "User deactivated successfully",
      });
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to deactivate user",
        variant: "destructive",
      });
    }
  };

  const togglePermission = (permission: string) => {
    setPermissions((prev) =>
      prev.includes(permission)
        ? prev.filter((p) => p !== permission)
        : [...prev, permission]
    );
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>User Details</SheetTitle>
        </SheetHeader>

        {isLoading || !user ? (
          <div className="space-y-4 mt-6">
            <Skeleton className="h-20 w-20 rounded-full mx-auto" />
            <Skeleton className="h-4 w-48 mx-auto" />
            <Skeleton className="h-4 w-32 mx-auto" />
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <div className="space-y-6 mt-6">
            {/* User Header */}
            <div className="flex flex-col items-center text-center space-y-3">
              <Avatar className="h-20 w-20">
                <AvatarFallback className="text-2xl">
                  {getInitials(user.name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lg">{user.name}</h3>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>

            {/* Role Selection */}
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">Owner</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="author">Author</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status */}
            <div className="space-y-2">
              <Label>Status</Label>
              <div>
                <Badge variant={user.status === "active" ? "default" : "secondary"}>
                  {user.status}
                </Badge>
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <Label className="text-muted-foreground">Joined</Label>
                <p className="mt-1">
                  {user.last_active ? formatDate(user.last_active) : "N/A"}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Last Active</Label>
                <p className="mt-1">
                  {user.last_active ? formatDate(user.last_active) : "Never"}
                </p>
              </div>
            </div>

            {/* Organization */}
            <div className="space-y-2">
              <Label className="text-muted-foreground">Organization</Label>
              <p>{user.org_name}</p>
            </div>

            {/* Activity Summary */}
            <div className="space-y-2">
              <Label className="text-muted-foreground">Activity Summary</Label>
              <div className="flex items-center gap-4 text-sm">
                <span>Books: {user.books_count}</span>
                <span>•</span>
                <span>Manuscripts: {user.manuscripts_count}</span>
                <span>•</span>
                <span>AI Tasks: {user.ai_tasks_count}</span>
              </div>
            </div>

            {/* Permissions */}
            <div className="space-y-3">
              <Label>Permissions</Label>
              <div className="space-y-2">
                {ALL_PERMISSIONS.map((permission) => (
                  <div key={permission} className="flex items-center space-x-2">
                    <Checkbox
                      id={permission}
                      checked={permissions.includes(permission)}
                      onCheckedChange={() => togglePermission(permission)}
                    />
                    <label
                      htmlFor={permission}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      {PERMISSION_LABELS[permission]}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3 pt-4 border-t">
              <Button
                className="w-full"
                onClick={handleSaveChanges}
                disabled={updateUser.isPending}
              >
                Save Changes
              </Button>
              <Button
                className="w-full"
                variant="outline"
                onClick={handleResetPassword}
                disabled={resetPassword.isPending}
              >
                Reset Password
              </Button>
              <Button
                className="w-full"
                variant="destructive"
                onClick={handleDeactivate}
                disabled={deactivateUser.isPending}
              >
                Deactivate User
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
