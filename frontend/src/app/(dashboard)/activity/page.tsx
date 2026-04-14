"use client";

import { useEffect, useState } from "react";
import { Activity as ActivityIcon, Download } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

interface ActivityEntry {
  id: string;
  user_id: string | null;
  action: string;
  description: string | null;
  resource_type: string | null;
  resource_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

const PAGE_SIZE = 50;

export default function ActivityPage() {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [action, setAction] = useState<string>("all");
  const [resourceType, setResourceType] = useState<string>("all");
  const [since, setSince] = useState<string>("");
  const [hasMore, setHasMore] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit: PAGE_SIZE,
        offset,
      };
      if (action !== "all") params.action = action;
      if (resourceType !== "all") params.resource_type = resourceType;
      if (since) params.since = new Date(since).toISOString();

      const res = await api.get("/api/v1/activity", { params });
      const data = res.data as { items: ActivityEntry[] };
      setEntries(data.items || []);
      setHasMore((data.items || []).length === PAGE_SIZE);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load activity";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, action, resourceType, since]);

  function exportCSV() {
    const header = [
      "timestamp",
      "user_id",
      "action",
      "description",
      "resource_type",
      "resource_id",
    ];
    const rows = entries.map((e) => [
      e.created_at || "",
      e.user_id || "",
      e.action,
      (e.description || "").replace(/"/g, '""'),
      e.resource_type || "",
      e.resource_id || "",
    ]);
    const csv = [header, ...rows]
      .map((r) => r.map((c) => `"${c}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activity-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ActivityIcon className="h-6 w-6" />
            Activity Log
          </h1>
          <p className="text-sm text-muted-foreground">
            All platform actions across your organization.
          </p>
        </div>
        <Button variant="outline" onClick={exportCSV} disabled={entries.length === 0}>
          <Download className="h-4 w-4 mr-2" /> Export CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 items-end">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Since</label>
          <Input
            type="date"
            value={since}
            onChange={(e) => {
              setSince(e.target.value);
              setOffset(0);
            }}
            className="w-[180px]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Action</label>
          <Select
            value={action}
            onValueChange={(v) => {
              setAction(v);
              setOffset(0);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All actions</SelectItem>
              <SelectItem value="created">Created</SelectItem>
              <SelectItem value="updated">Updated</SelectItem>
              <SelectItem value="deleted">Deleted</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="exported">Exported</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Resource Type</label>
          <Select
            value={resourceType}
            onValueChange={(v) => {
              setResourceType(v);
              setOffset(0);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All resources</SelectItem>
              <SelectItem value="project">Project</SelectItem>
              <SelectItem value="book">Book</SelectItem>
              <SelectItem value="chapter">Chapter</SelectItem>
              <SelectItem value="pipeline">Pipeline</SelectItem>
              <SelectItem value="campaign">Campaign</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading && entries.length === 0 ? (
        <div className="space-y-2">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={<ActivityIcon className="h-10 w-10" />}
          title="No activity yet"
          description="Activity will appear here as you and your team use the platform."
        />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {e.created_at
                      ? new Date(e.created_at).toLocaleString()
                      : "—"}
                  </TableCell>
                  <TableCell className="font-medium">{e.action}</TableCell>
                  <TableCell className="text-sm">
                    {e.resource_type || "—"}
                    {e.resource_id ? (
                      <span className="text-xs text-muted-foreground ml-1">
                        #{e.resource_id.slice(0, 8)}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {e.description || ""}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between pt-2">
            <p className="text-sm text-muted-foreground">
              Showing {offset + 1}-{offset + entries.length}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                Prev
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasMore}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
