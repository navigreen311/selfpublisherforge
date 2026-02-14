"use client";

import { useState, useMemo } from "react";
import { format, isPast, parseISO } from "date-fns";
import { Clock, Plus, Edit2, XCircle, CalendarClock, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { useProjects } from "@/modules/projects/hooks";
import {
  useScheduledChanges,
  useCreateScheduledChange,
  useCancelScheduledChange,
} from "../hooks";
import type { ScheduledPriceChange, ScheduledChangePayload } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ScheduledPriceChangesProps {
  className?: string;
}

interface FormState {
  book_id: string;
  new_price: string;
  current_price: string;
  execute_at: string;
  reason: string;
  reason_type: string;
  auto_revert: boolean;
  revert_price: string;
  revert_at: string;
}

const INITIAL_FORM: FormState = {
  book_id: "",
  new_price: "",
  current_price: "",
  execute_at: "",
  reason: "",
  reason_type: "",
  auto_revert: false,
  revert_price: "",
  revert_at: "",
};

const REASON_OPTIONS = [
  { value: "promo", label: "Promo" },
  { value: "strategy", label: "Strategy" },
  { value: "launch", label: "Launch" },
  { value: "season", label: "Season" },
  { value: "other", label: "Other" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatShortDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM d");
  } catch {
    return dateStr;
  }
}

function formatPrice(value: number | undefined): string {
  if (value === undefined || value === null) return "--";
  return `$${value.toFixed(2)}`;
}

function toLocalDatetimeString(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ScheduleItemSkeleton() {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <Skeleton className="h-5 w-5 rounded-full" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-32 ml-auto" />
    </div>
  );
}

function StatusBadge({ status }: { status: ScheduledPriceChange["status"] }) {
  const variants: Record<
    ScheduledPriceChange["status"],
    { label: string; className: string }
  > = {
    pending: {
      label: "Pending",
      className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    },
    executed: {
      label: "Executed",
      className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    },
    cancelled: {
      label: "Cancelled",
      className: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
    },
  };

  const v = variants[status];
  return <Badge className={v.className}>{v.label}</Badge>;
}

interface ChangeItemProps {
  change: ScheduledPriceChange;
  bookName?: string;
  onEdit: (change: ScheduledPriceChange) => void;
  onCancel: (id: string) => void;
  isCancelling: boolean;
}

function ChangeItem({ change, bookName, onEdit, onCancel, isCancelling }: ChangeItemProps) {
  const isPastChange = isPast(parseISO(change.execute_at));
  const isActionable = change.status === "pending" && !isPastChange;

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
      <Clock className="h-4 w-4 text-muted-foreground shrink-0" />

      <span className="text-sm font-medium whitespace-nowrap">
        {formatShortDate(change.execute_at)}
      </span>

      <span className="text-sm text-muted-foreground truncate min-w-0">
        {bookName || change.book_id}
      </span>

      <span className="text-sm font-medium whitespace-nowrap">
        {formatPrice(change.current_price)}
        <ArrowRight className="inline h-3 w-3 mx-1 text-muted-foreground" />
        {formatPrice(change.new_price)}
      </span>

      {change.reason && (
        <span className="text-xs text-muted-foreground whitespace-nowrap hidden sm:inline">
          ({change.reason})
        </span>
      )}

      <StatusBadge status={change.status} />

      {isActionable && (
        <div className="flex items-center gap-1 ml-auto shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onEdit(change)}
          >
            <Edit2 className="h-3.5 w-3.5" />
            <span className="sr-only">Edit</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive"
            disabled={isCancelling}
            onClick={() => onCancel(change.id)}
          >
            <XCircle className="h-3.5 w-3.5" />
            <span className="sr-only">Cancel</span>
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function ScheduledPriceChanges({ className }: ScheduledPriceChangesProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingChange, setEditingChange] = useState<ScheduledPriceChange | null>(null);
  const [form, setForm] = useState<FormState>(INITIAL_FORM);

  // Data hooks
  const { data: changes, isLoading } = useScheduledChanges();
  const { data: projects } = useProjects();
  const createMutation = useCreateScheduledChange();
  const cancelMutation = useCancelScheduledChange();

  // Build a lookup map for book names
  const bookNameMap = useMemo(() => {
    const map = new Map<string, string>();
    if (projects) {
      for (const project of projects) {
        map.set(project.id, project.title);
        if (project.books) {
          for (const book of project.books) {
            map.set(book.id, book.title);
          }
        }
      }
    }
    return map;
  }, [projects]);

  // Split changes into upcoming and past
  const { upcoming, past } = useMemo(() => {
    if (!changes) return { upcoming: [], past: [] };

    const sorted = [...changes].sort(
      (a, b) => new Date(a.execute_at).getTime() - new Date(b.execute_at).getTime()
    );

    const upcomingItems: ScheduledPriceChange[] = [];
    const pastItems: ScheduledPriceChange[] = [];

    for (const change of sorted) {
      if (change.status === "pending" && !isPast(parseISO(change.execute_at))) {
        upcomingItems.push(change);
      } else {
        pastItems.push(change);
      }
    }

    return { upcoming: upcomingItems, past: pastItems };
  }, [changes]);

  // ---------------------------------------------------------------------------
  // Dialog handlers
  // ---------------------------------------------------------------------------

  function openCreateDialog() {
    setEditingChange(null);
    setForm({
      ...INITIAL_FORM,
      execute_at: toLocalDatetimeString(new Date(Date.now() + 24 * 60 * 60 * 1000)),
    });
    setDialogOpen(true);
  }

  function openEditDialog(change: ScheduledPriceChange) {
    setEditingChange(change);
    setForm({
      book_id: change.book_id,
      new_price: String(change.new_price),
      current_price: change.current_price ? String(change.current_price) : "",
      execute_at: toLocalDatetimeString(parseISO(change.execute_at)),
      reason: change.reason || "",
      reason_type: "",
      auto_revert: !!(change.revert_price && change.revert_at),
      revert_price: change.revert_price ? String(change.revert_price) : "",
      revert_at: change.revert_at
        ? toLocalDatetimeString(parseISO(change.revert_at))
        : "",
    });
    setDialogOpen(true);
  }

  function handleCancel(id: string) {
    if (!window.confirm("Are you sure you want to cancel this scheduled price change?")) {
      return;
    }
    cancelMutation.mutate(id);
  }

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleReasonTypeChange(value: string) {
    updateField("reason_type", value);
    if (value !== "other") {
      const label = REASON_OPTIONS.find((o) => o.value === value)?.label || value;
      updateField("reason", label);
    } else {
      updateField("reason", "");
    }
  }

  function handleSubmit() {
    // Validation
    const newPrice = parseFloat(form.new_price);
    if (isNaN(newPrice) || newPrice <= 0) {
      toast.error("Please enter a valid new price");
      return;
    }

    if (!form.book_id) {
      toast.error("Please select a book");
      return;
    }

    const executeAt = new Date(form.execute_at);
    if (isNaN(executeAt.getTime()) || executeAt <= new Date()) {
      toast.error("Execute date must be in the future");
      return;
    }

    const payload: ScheduledChangePayload = {
      book_id: form.book_id,
      new_price: newPrice,
      execute_at: executeAt.toISOString(),
    };

    if (form.current_price) {
      const cp = parseFloat(form.current_price);
      if (!isNaN(cp)) payload.current_price = cp;
    }

    if (form.reason.trim()) {
      payload.reason = form.reason.trim();
    }

    if (form.auto_revert) {
      const revertPrice = parseFloat(form.revert_price);
      if (isNaN(revertPrice) || revertPrice <= 0) {
        toast.error("Please enter a valid revert price");
        return;
      }
      const revertAt = new Date(form.revert_at);
      if (isNaN(revertAt.getTime()) || revertAt <= executeAt) {
        toast.error("Revert date must be after the execute date");
        return;
      }
      payload.revert_price = revertPrice;
      payload.revert_at = revertAt.toISOString();
    }

    createMutation.mutate(payload, {
      onSuccess: () => {
        setDialogOpen(false);
        setEditingChange(null);
        setForm(INITIAL_FORM);
      },
    });
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold">Scheduled Price Changes</CardTitle>
        <Button size="sm" onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-1" />
          Schedule
        </Button>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Loading State */}
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <ScheduleItemSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && (!changes || changes.length === 0) && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CalendarClock className="h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">
              No scheduled price changes. Schedule your first one!
            </p>
          </div>
        )}

        {/* Upcoming Changes */}
        {!isLoading && upcoming.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Upcoming
            </h4>
            {upcoming.map((change) => (
              <ChangeItem
                key={change.id}
                change={change}
                bookName={bookNameMap.get(change.book_id)}
                onEdit={openEditDialog}
                onCancel={handleCancel}
                isCancelling={cancelMutation.isPending}
              />
            ))}
          </div>
        )}

        {/* Past Changes */}
        {!isLoading && past.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Past Changes
            </h4>
            {past.map((change) => (
              <ChangeItem
                key={change.id}
                change={change}
                bookName={bookNameMap.get(change.book_id)}
                onEdit={openEditDialog}
                onCancel={handleCancel}
                isCancelling={cancelMutation.isPending}
              />
            ))}
          </div>
        )}
      </CardContent>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingChange ? "Edit Scheduled Change" : "Schedule Price Change"}
            </DialogTitle>
            <DialogDescription>
              {editingChange
                ? "Update the details for this scheduled price change."
                : "Set up a future price change for one of your books."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-2">
            {/* Book Select */}
            <div className="grid gap-2">
              <Label htmlFor="schedule-book">Book</Label>
              <Select
                value={form.book_id}
                onValueChange={(value) => updateField("book_id", value)}
              >
                <SelectTrigger id="schedule-book">
                  <SelectValue placeholder="Select a book" />
                </SelectTrigger>
                <SelectContent>
                  {projects?.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Price Inputs */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="schedule-current-price">Current Price</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="schedule-current-price"
                    type="number"
                    step="0.01"
                    min="0"
                    className="pl-7"
                    placeholder="9.99"
                    value={form.current_price}
                    onChange={(e) => updateField("current_price", e.target.value)}
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="schedule-new-price">New Price *</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="schedule-new-price"
                    type="number"
                    step="0.01"
                    min="0"
                    className="pl-7"
                    placeholder="4.99"
                    value={form.new_price}
                    onChange={(e) => updateField("new_price", e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Execute At */}
            <div className="grid gap-2">
              <Label htmlFor="schedule-execute-at">Execute At *</Label>
              <Input
                id="schedule-execute-at"
                type="datetime-local"
                value={form.execute_at}
                onChange={(e) => updateField("execute_at", e.target.value)}
              />
            </div>

            {/* Reason */}
            <div className="grid gap-2">
              <Label>Reason</Label>
              <div className="flex gap-2">
                <Select
                  value={form.reason_type}
                  onValueChange={handleReasonTypeChange}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {REASON_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="e.g. BookBub promo"
                  value={form.reason}
                  onChange={(e) => updateField("reason", e.target.value)}
                  className="flex-1"
                />
              </div>
            </div>

            {/* Auto-Revert */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="schedule-auto-revert"
                  checked={form.auto_revert}
                  onCheckedChange={(checked) =>
                    updateField("auto_revert", checked === true)
                  }
                />
                <Label htmlFor="schedule-auto-revert" className="text-sm font-normal cursor-pointer">
                  Revert to original price after promotion
                </Label>
              </div>

              {form.auto_revert && (
                <div className="grid grid-cols-2 gap-4 pl-6">
                  <div className="grid gap-2">
                    <Label htmlFor="schedule-revert-price">Revert Price</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                        $
                      </span>
                      <Input
                        id="schedule-revert-price"
                        type="number"
                        step="0.01"
                        min="0"
                        className="pl-7"
                        placeholder="9.99"
                        value={form.revert_price}
                        onChange={(e) => updateField("revert_price", e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="schedule-revert-at">Revert At</Label>
                    <Input
                      id="schedule-revert-at"
                      type="datetime-local"
                      value={form.revert_at}
                      onChange={(e) => updateField("revert_at", e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending
                ? "Scheduling..."
                : editingChange
                  ? "Update Schedule"
                  : "Schedule Change"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
