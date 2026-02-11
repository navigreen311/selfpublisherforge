"use client";

import { useState } from "react";
import { useAuditLog } from "../hooks";
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
import type { AuditLogFilters } from "../types";

export function AuditLog() {
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useAuditLog(filters, page, 50);

  const handleActionFilter = (action: string) => {
    setFilters((prev) => ({
      ...prev,
      action: action === "all" ? undefined : action,
    }));
    setPage(1);
  };

  const handleResourceFilter = (resourceType: string) => {
    setFilters((prev) => ({
      ...prev,
      resource_type: resourceType === "all" ? undefined : resourceType,
    }));
    setPage(1);
  };

  const handleDateRangeChange = (field: "start_date" | "end_date", value: string) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value || undefined,
    }));
    setPage(1);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load audit log. Please try again.</p>
      </div>
    );
  }

  const getActionBadgeVariant = (action: string) => {
    if (action.includes("create")) return "default";
    if (action.includes("update")) return "secondary";
    if (action.includes("delete")) return "destructive";
    return "outline";
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Select onValueChange={handleActionFilter} defaultValue="all">
          <SelectTrigger>
            <SelectValue placeholder="Filter by action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            <SelectItem value="user.login">User Login</SelectItem>
            <SelectItem value="user.logout">User Logout</SelectItem>
            <SelectItem value="user.create">User Create</SelectItem>
            <SelectItem value="user.update">User Update</SelectItem>
            <SelectItem value="user.delete">User Delete</SelectItem>
            <SelectItem value="org.create">Org Create</SelectItem>
            <SelectItem value="org.update">Org Update</SelectItem>
            <SelectItem value="subscription.create">Subscription Create</SelectItem>
            <SelectItem value="subscription.cancel">Subscription Cancel</SelectItem>
          </SelectContent>
        </Select>

        <Select onValueChange={handleResourceFilter} defaultValue="all">
          <SelectTrigger>
            <SelectValue placeholder="Filter by resource" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Resources</SelectItem>
            <SelectItem value="user">User</SelectItem>
            <SelectItem value="organization">Organization</SelectItem>
            <SelectItem value="subscription">Subscription</SelectItem>
            <SelectItem value="api_key">API Key</SelectItem>
            <SelectItem value="project">Project</SelectItem>
          </SelectContent>
        </Select>

        <Input
          type="date"
          placeholder="Start date"
          onChange={(e) => handleDateRangeChange("start_date", e.target.value)}
        />

        <Input
          type="date"
          placeholder="End date"
          onChange={(e) => handleDateRangeChange("end_date", e.target.value)}
        />
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Resource ID</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No audit log entries found
                  </TableCell>
                </TableRow>
              ) : (
                data?.items.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="text-sm">
                      {new Date(entry.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm">{entry.user_email}</TableCell>
                    <TableCell>
                      <Badge variant={getActionBadgeVariant(entry.action)}>
                        {entry.action}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{entry.resource_type}</TableCell>
                    <TableCell className="text-sm text-muted-foreground font-mono">
                      {entry.resource_id ? (
                        entry.resource_id.length > 12
                          ? `${entry.resource_id.substring(0, 12)}...`
                          : entry.resource_id
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {entry.ip_address || "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {entry.details ? (
                        <details className="cursor-pointer">
                          <summary className="text-blue-600 hover:underline">
                            View
                          </summary>
                          <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto max-w-md">
                            {JSON.stringify(entry.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        "—"
                      )}
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
            Showing {data.items.length} of {data.total} entries
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
    </div>
  );
}
