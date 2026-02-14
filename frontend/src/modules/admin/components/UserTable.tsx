"use client";

import { useState } from "react";
import { UserPlus } from "lucide-react";
import { useAdminUsers } from "../hooks";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { UserFilters } from "../types";
import { UserDetailPanel } from "./UserDetailPanel";
import { InviteUserModal } from "./InviteUserModal";

export function UserTable() {
  const [filters, setFilters] = useState<UserFilters>({});
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [inviteModalOpen, setInviteModalOpen] = useState(false);

  const { data, isLoading, error } = useAdminUsers(filters, page, 20);

  const handleSearch = (value: string) => {
    setSearchInput(value);
    setFilters((prev) => ({ ...prev, search: value }));
    setPage(1);
  };

  const handleStatusFilter = (status: string) => {
    setFilters((prev) => {
      const newFilters = { ...prev };
      if (status === "all") {
        delete newFilters.is_active;
        delete newFilters.is_banned;
      } else if (status === "active") {
        newFilters.is_active = true;
        delete newFilters.is_banned;
      } else if (status === "inactive") {
        newFilters.is_active = false;
        delete newFilters.is_banned;
      }
      return newFilters;
    });
    setPage(1);
  };

  const handleRoleFilter = (role: string) => {
    setFilters((prev) => ({
      ...prev,
      role: role === "all" ? undefined : role,
    }));
    setPage(1);
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getStatusBadge = (user: { is_active: boolean; is_banned: boolean }) => {
    if (user.is_banned) {
      return <Badge variant="destructive">Inactive</Badge>;
    }
    if (user.is_active) {
      return <span className="text-green-500">🟢</span>;
    }
    return <span className="text-yellow-500">🟡</span>;
  };

  const formatLastActive = (lastLogin: string | null) => {
    if (!lastLogin) return "Never";
    const date = new Date(lastLogin);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load users. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Users</h2>
        <Button onClick={() => setInviteModalOpen(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite User
        </Button>
      </div>

      {/* Search Bar */}
      <Input
        placeholder="Search by name or email..."
        value={searchInput}
        onChange={(e) => handleSearch(e.target.value)}
        className="max-w-md"
      />

      {/* Filter Row */}
      <div className="flex gap-4">
        <Select onValueChange={handleStatusFilter} defaultValue="all">
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>

        <Select onValueChange={handleRoleFilter} defaultValue="all">
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="owner">Owner</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="editor">Editor</SelectItem>
            <SelectItem value="author">Author</SelectItem>
            <SelectItem value="viewer">Viewer</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                data?.items.map((user) => (
                  <TableRow
                    key={user.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => setSelectedUserId(user.id)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="text-xs">
                            {getInitials(user.name)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium">{user.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(user)}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatLastActive(user.last_login_at)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {data.items.length} of {data.total} users
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <div className="flex items-center gap-2">
              <span className="text-sm">
                Page {page} of {data.total_pages}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page === data.total_pages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Detail Panel */}
      <UserDetailPanel
        open={!!selectedUserId}
        onOpenChange={(open) => !open && setSelectedUserId(null)}
        userId={selectedUserId || ""}
      />

      {/* Invite Modal */}
      <InviteUserModal
        open={inviteModalOpen}
        onOpenChange={setInviteModalOpen}
      />
    </div>
  );
}
