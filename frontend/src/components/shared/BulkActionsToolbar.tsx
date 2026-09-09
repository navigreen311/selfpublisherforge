"use client";

import * as React from "react";
import {
  Archive,
  Download,
  Tag,
  Trash2,
  DollarSign,
  X,
  CheckSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  useBulkBooks,
  exportMetadataCsv,
  type BulkAction,
} from "@/modules/projects/bulk-hooks";

export interface BulkActionsToolbarProps {
  /** IDs of currently selected items. */
  selectedIds: string[];
  /** Total item count (for the "Select All" label). */
  totalCount: number;
  /** Whether all visible items are selected. */
  allSelected: boolean;
  /** Toggle select-all state. */
  onToggleSelectAll: () => void;
  /** Clear the selection and exit bulk mode. */
  onClearSelection: () => void;
  /** Optional selected-items preview used in the delete confirmation. */
  selectedPreview?: Array<{ id: string; title: string }>;
}

/**
 * Bulk actions toolbar used in multi-select mode on list/grid pages.
 *
 * Actions: archive, delete (with DELETE confirmation), change_price (prompt),
 * add_tags (prompt), export_metadata_csv (blob download).
 */
export function BulkActionsToolbar({
  selectedIds,
  totalCount,
  allSelected,
  onToggleSelectAll,
  onClearSelection,
  selectedPreview,
}: BulkActionsToolbarProps) {
  const bulk = useBulkBooks();
  const [confirmDelete, setConfirmDelete] = React.useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = React.useState("");
  const [priceOpen, setPriceOpen] = React.useState(false);
  const [priceValue, setPriceValue] = React.useState<string>("");
  const [tagsOpen, setTagsOpen] = React.useState(false);
  const [tagsValue, setTagsValue] = React.useState<string>("");
  const [busyAction, setBusyAction] = React.useState<BulkAction | null>(null);

  const runSimple = async (action: BulkAction) => {
    if (selectedIds.length === 0) return;
    setBusyAction(action);
    try {
      await bulk.mutateAsync({ action, book_ids: selectedIds });
      onClearSelection();
    } finally {
      setBusyAction(null);
    }
  };

  const runChangePrice = async () => {
    const price = Number(priceValue);
    if (!Number.isFinite(price) || price < 0) return;
    setBusyAction("change_price");
    try {
      await bulk.mutateAsync({
        action: "change_price",
        book_ids: selectedIds,
        params: { price },
      });
      setPriceOpen(false);
      setPriceValue("");
      onClearSelection();
    } finally {
      setBusyAction(null);
    }
  };

  const runAddTags = async () => {
    const tags = tagsValue
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (tags.length === 0) return;
    setBusyAction("add_tags");
    try {
      await bulk.mutateAsync({
        action: "add_tags",
        book_ids: selectedIds,
        params: { tags },
      });
      setTagsOpen(false);
      setTagsValue("");
      onClearSelection();
    } finally {
      setBusyAction(null);
    }
  };

  const runExport = async () => {
    if (selectedIds.length === 0) return;
    setBusyAction("export_metadata_csv");
    try {
      await exportMetadataCsv(selectedIds);
    } finally {
      setBusyAction(null);
    }
  };

  const runDelete = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setBusyAction("delete");
    try {
      await bulk.mutateAsync({ action: "delete", book_ids: selectedIds });
      setConfirmDelete(false);
      setDeleteConfirmText("");
      onClearSelection();
    } finally {
      setBusyAction(null);
    }
  };

  const disabled = selectedIds.length === 0 || busyAction !== null;

  return (
    <div
      role="toolbar"
      aria-label="Bulk actions"
      className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 p-2"
    >
      <Button
        variant="outline"
        size="sm"
        onClick={onToggleSelectAll}
        aria-label={allSelected ? "Deselect all" : "Select all"}
      >
        <CheckSquare className="mr-2 h-4 w-4" />
        {allSelected ? "Deselect All" : "Select All"}
      </Button>
      <span className="text-sm text-muted-foreground" aria-live="polite">
        {selectedIds.length} of {totalCount} selected
      </span>

      <div className="ml-auto flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" disabled={disabled}>
              Bulk Actions
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => runSimple("archive")}
              disabled={disabled}
            >
              <Archive className="mr-2 h-4 w-4" /> Archive Selected
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => setPriceOpen(true)}
              disabled={disabled}
            >
              <DollarSign className="mr-2 h-4 w-4" /> Change Price
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => setTagsOpen(true)}
              disabled={disabled}
            >
              <Tag className="mr-2 h-4 w-4" /> Add Tags
            </DropdownMenuItem>
            <DropdownMenuItem onClick={runExport} disabled={disabled}>
              <Download className="mr-2 h-4 w-4" /> Export Metadata CSV
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => setConfirmDelete(true)}
              disabled={disabled}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" /> Delete Selected
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          aria-label="Exit bulk mode"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedIds.length} book(s)?</DialogTitle>
            <DialogDescription>
              This will permanently delete the selected books. This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {selectedPreview && selectedPreview.length > 0 && (
            <ul className="max-h-40 overflow-auto text-sm space-y-1">
              {selectedPreview.slice(0, 10).map((p) => (
                <li key={p.id} className="truncate">
                  {"\u2022"} {p.title}
                </li>
              ))}
              {selectedPreview.length > 10 && (
                <li className="text-muted-foreground">
                  ...and {selectedPreview.length - 10} more
                </li>
              )}
            </ul>
          )}
          <div className="space-y-2">
            <Label htmlFor="bulk-delete-confirm">
              Type &quot;DELETE&quot; to confirm
            </Label>
            <Input
              id="bulk-delete-confirm"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              autoComplete="off"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setConfirmDelete(false);
                setDeleteConfirmText("");
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={runDelete}
              disabled={
                deleteConfirmText !== "DELETE" || busyAction === "delete"
              }
            >
              Delete Forever
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Change price dialog */}
      <Dialog open={priceOpen} onOpenChange={setPriceOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change price for {selectedIds.length} book(s)</DialogTitle>
            <DialogDescription>
              Sets the metadata.price field on all selected books.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="bulk-price">New price (USD)</Label>
            <Input
              id="bulk-price"
              type="number"
              min={0}
              step="0.01"
              value={priceValue}
              onChange={(e) => setPriceValue(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPriceOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={runChangePrice}
              disabled={
                !priceValue ||
                Number(priceValue) < 0 ||
                busyAction === "change_price"
              }
            >
              Apply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add tags dialog */}
      <Dialog open={tagsOpen} onOpenChange={setTagsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add tags to {selectedIds.length} book(s)</DialogTitle>
            <DialogDescription>
              Comma-separated list of tags to merge into existing tags.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="bulk-tags">Tags</Label>
            <Input
              id="bulk-tags"
              value={tagsValue}
              onChange={(e) => setTagsValue(e.target.value)}
              placeholder="fantasy, bestseller, 2026"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTagsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={runAddTags}
              disabled={!tagsValue.trim() || busyAction === "add_tags"}
            >
              Apply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
