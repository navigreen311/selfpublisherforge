"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditLog } from "../hooks";
import type { AuditLogFilters } from "../types";

// Helper to get user initials from email
function getInitials(email: string): string {
  const name = email.split("@")[0];
  const parts = name.split(/[._-]/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

// Helper to format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600) {
    const mins = Math.floor(diffInSeconds / 60);
    return `${mins} min${mins > 1 ? "s" : ""} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  }
  if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  }
  return date.toLocaleDateString();
}

// Helper to format action description
function formatActionDescription(entry: any): string {
  const action = entry.action.toLowerCase();
  const resourceType = entry.resource_type?.toLowerCase() || "item";

  // Extract resource name from details if available
  let resourceName = "";
  if (entry.details && typeof entry.details === "object") {
    resourceName = (entry.details as any).name || (entry.details as any).title || "";
  }

  if (action.includes("create")) {
    return resourceName
      ? `created a new ${resourceType} "${resourceName}"`
      : `created a new ${resourceType}`;
  }
  if (action.includes("update")) {
    return resourceName
      ? `updated ${resourceType} "${resourceName}"`
      : `updated a ${resourceType}`;
  }
  if (action.includes("delete")) {
    return resourceName
      ? `deleted ${resourceType} "${resourceName}"`
      : `deleted a ${resourceType}`;
  }
  if (action.includes("export")) {
    return resourceName
      ? `exported ${resourceType} "${resourceName}"`
      : `exported a ${resourceType}`;
  }
  if (action.includes("generate")) {
    return resourceName
      ? `generated ${resourceType} "${resourceName}"`
      : `generated a ${resourceType}`;
  }
  if (action.includes("login")) {
    return "logged in";
  }
  if (action.includes("logout")) {
    return "logged out";
  }

  // Fallback
  return `performed ${action} on ${resourceType}`;
}

export function AuditLog() {
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useAuditLog(filters, page, 20);

  const handleActionFilter = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      action: value === "all" ? undefined : value,
    }));
    setPage(1);
  };

  const handleResourceFilter = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      resource_type: value === "all" ? undefined : value,
    }));
    setPage(1);
  };

  const handleDateChange = (field: "start_date" | "end_date", value: string) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value || undefined,
    }));
    setPage(1);
  };

  const handleLoadMore = () => {
    setPage((p) => p + 1);
  };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>Failed to load activity log. Please try again.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        {/* Filter Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <Select onValueChange={handleActionFilter} defaultValue="all">
            <SelectTrigger>
              <SelectValue placeholder="All Actions" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Actions</SelectItem>
              <SelectItem value="create">Created</SelectItem>
              <SelectItem value="update">Updated</SelectItem>
              <SelectItem value="delete">Deleted</SelectItem>
              <SelectItem value="export">Exported</SelectItem>
              <SelectItem value="generate">Generated</SelectItem>
            </SelectContent>
          </Select>

          <Select onValueChange={handleResourceFilter} defaultValue="all">
            <SelectTrigger>
              <SelectValue placeholder="All Resources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Resources</SelectItem>
              <SelectItem value="book">Book</SelectItem>
              <SelectItem value="manuscript">Manuscript</SelectItem>
              <SelectItem value="agent_task">Agent Task</SelectItem>
              <SelectItem value="cover">Cover</SelectItem>
              <SelectItem value="export">Export</SelectItem>
            </SelectContent>
          </Select>

          <Input
            type="date"
            placeholder="From"
            onChange={(e) => handleDateChange("start_date", e.target.value)}
          />

          <Input
            type="date"
            placeholder="To"
            onChange={(e) => handleDateChange("end_date", e.target.value)}
          />
        </div>

        {/* Activity List */}
        <div className="space-y-4">
          {isLoading && page === 1 ? (
            <>
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-start gap-3">
                  <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                </div>
              ))}
            </>
          ) : data?.items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No activity found</p>
            </div>
          ) : (
            <>
              {data?.items.map((entry) => (
                <div key={entry.id} className="flex items-start gap-3 pb-4 border-b last:border-b-0">
                  {/* User Avatar */}
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium text-primary">
                      {getInitials(entry.user_email)}
                    </span>
                  </div>

                  {/* Activity Details */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">
                      <span className="font-medium">{entry.user_email}</span>
                      {" "}
                      <span className="text-muted-foreground">
                        {formatActionDescription(entry)}
                      </span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatRelativeTime(entry.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Load More Button */}
        {data && data.total_pages > page && (
          <div className="mt-6 text-center">
            <Button
              variant="outline"
              onClick={handleLoadMore}
              disabled={isLoading}
            >
              {isLoading ? "Loading..." : "Load More"}
            </Button>
          </div>
        )}

        {/* Pagination Info */}
        {data && data.items.length > 0 && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Showing {data.items.length} of {data.total} entries
            {data.total_pages > 1 && ` (page ${page} of ${data.total_pages})`}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
