"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  Plus,
  Barcode,
  Download,
  BookOpen,
  Hash,
  CheckCircle2,
  Clock,
  Circle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ISBNStatus = "available" | "assigned" | "used";

export interface ISBNRecord {
  id: string;
  isbn: string;
  publisherName: string | null;
  assignedToBookType: string | null;
  assignedToBookId: string | null;
  assignedToBookTitle: string | null;
  barcodeData: string | null;
  status: ISBNStatus;
}

export interface BookOption {
  id: string;
  title: string;
  bookType: string;
}

export interface PoolStats {
  total: number;
  assigned: number;
  available: number;
}

export interface ISBNManagerProps {
  records: ISBNRecord[];
  poolStats: PoolStats;
  bookOptions: BookOption[];
  onAddISBN: (isbn: string, publisherName: string) => void;
  onAssignISBN: (isbnId: string, bookType: string, bookId: string) => void;
  onDownloadBarcode: (isbnId: string) => void;
  isAdding: boolean;
  isAssigning: boolean;
}

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: ISBNStatus }) {
  if (status === "available") {
    return (
      <Badge variant="secondary" className="gap-1">
        <Circle className="h-2 w-2 fill-green-500 text-green-500" />
        Available
      </Badge>
    );
  }
  if (status === "assigned") {
    return (
      <Badge variant="default" className="gap-1">
        <Clock className="h-2 w-2" />
        Assigned
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="gap-1">
      <CheckCircle2 className="h-2 w-2" />
      Used
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Pool stats display
// ---------------------------------------------------------------------------

function PoolStatsDisplay({ stats }: { stats: PoolStats }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <Card className="p-3 text-center">
        <p className="text-2xl font-bold">{stats.total}</p>
        <p className="text-xs text-muted-foreground">Total</p>
      </Card>
      <Card className="p-3 text-center">
        <p className="text-2xl font-bold text-blue-600">{stats.assigned}</p>
        <p className="text-xs text-muted-foreground">Assigned</p>
      </Card>
      <Card className="p-3 text-center">
        <p className="text-2xl font-bold text-green-600">{stats.available}</p>
        <p className="text-xs text-muted-foreground">Available</p>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Add ISBN form
// ---------------------------------------------------------------------------

function AddISBNForm({
  onSubmit,
  isAdding,
}: {
  onSubmit: (isbn: string, publisher: string) => void;
  isAdding: boolean;
}) {
  const [isbn, setISBN] = React.useState("");
  const [publisher, setPublisher] = React.useState("");
  const [showForm, setShowForm] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isbn.trim()) return;
    onSubmit(isbn.trim(), publisher.trim());
    setISBN("");
    setPublisher("");
    setShowForm(false);
  };

  if (!showForm) {
    return (
      <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
        <Plus className="mr-1 h-4 w-4" />
        Add ISBN
      </Button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
      <div className="space-y-1">
        <Label htmlFor="isbn-input">ISBN-13</Label>
        <Input
          id="isbn-input"
          value={isbn}
          onChange={(e) => setISBN(e.target.value)}
          placeholder="978-0-123456-78-9"
          maxLength={17}
        />
        <p className="text-xs text-muted-foreground">
          Enter a valid ISBN-13 with or without dashes.
        </p>
      </div>
      <div className="space-y-1">
        <Label htmlFor="publisher-input">Publisher Name</Label>
        <Input
          id="publisher-input"
          value={publisher}
          onChange={(e) => setPublisher(e.target.value)}
          placeholder="Your publishing imprint"
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={!isbn.trim() || isAdding}>
          {isAdding ? "Adding..." : "Add to Pool"}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowForm(false)}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Assign ISBN dropdown
// ---------------------------------------------------------------------------

function AssignISBNDropdown({
  record,
  bookOptions,
  onAssign,
  isAssigning,
}: {
  record: ISBNRecord;
  bookOptions: BookOption[];
  onAssign: (isbnId: string, bookType: string, bookId: string) => void;
  isAssigning: boolean;
}) {
  const [selectedBookId, setSelectedBookId] = React.useState("");

  const selectedBook = bookOptions.find((b) => b.id === selectedBookId);

  return (
    <div className="flex items-center gap-2">
      <Select value={selectedBookId} onValueChange={setSelectedBookId}>
        <SelectTrigger className="h-8 w-48 text-xs">
          <SelectValue placeholder="Assign to book..." />
        </SelectTrigger>
        <SelectContent>
          {bookOptions.map((book) => (
            <SelectItem key={book.id} value={book.id}>
              {book.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        variant="outline"
        size="sm"
        className="h-8"
        disabled={!selectedBookId || isAssigning}
        onClick={() => {
          if (selectedBook) {
            onAssign(record.id, selectedBook.bookType, selectedBook.id);
            setSelectedBookId("");
          }
        }}
      >
        Assign
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Barcode preview
// ---------------------------------------------------------------------------

function BarcodePreview({
  record,
  onDownload,
}: {
  record: ISBNRecord;
  onDownload: () => void;
}) {
  if (!record.barcodeData) {
    return <span className="text-xs text-muted-foreground">--</span>;
  }

  return (
    <div className="flex items-center gap-2">
      <img
        src={`data:image/png;base64,${record.barcodeData}`}
        alt={`Barcode for ${record.isbn}`}
        className="h-8 w-auto"
      />
      <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onDownload}>
        <Download className="h-3 w-3" />
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ISBNManager({
  records,
  poolStats,
  bookOptions,
  onAddISBN,
  onAssignISBN,
  onDownloadBarcode,
  isAdding,
  isAssigning,
}: ISBNManagerProps) {
  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Pool stats                                                        */}
      {/* ----------------------------------------------------------------- */}
      <PoolStatsDisplay stats={poolStats} />

      {/* ----------------------------------------------------------------- */}
      {/* Add ISBN                                                          */}
      {/* ----------------------------------------------------------------- */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">ISBN Pool</h3>
        <AddISBNForm onSubmit={onAddISBN} isAdding={isAdding} />
      </div>

      <Separator />

      {/* ----------------------------------------------------------------- */}
      {/* ISBN table                                                        */}
      {/* ----------------------------------------------------------------- */}
      {records.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No ISBNs in pool. Add ISBNs to start managing your inventory.
        </p>
      ) : (
        <div className="space-y-2">
          {/* Header */}
          <div className="hidden items-center gap-3 border-b px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground md:flex">
            <span className="w-36">ISBN</span>
            <span className="w-32">Publisher</span>
            <span className="w-40">Assigned To</span>
            <span className="w-28">Barcode</span>
            <span className="w-24">Status</span>
            <span className="flex-1">Actions</span>
          </div>

          {/* Rows */}
          {records.map((record) => (
            <Card key={record.id} className="flex flex-col gap-2 p-3 md:flex-row md:items-center md:gap-3">
              {/* ISBN */}
              <div className="flex items-center gap-2 md:w-36">
                <Hash className="h-4 w-4 shrink-0 text-muted-foreground md:hidden" />
                <span className="font-mono text-sm font-medium">{record.isbn}</span>
              </div>

              {/* Publisher */}
              <div className="md:w-32">
                <span className="text-sm text-muted-foreground">
                  {record.publisherName || "--"}
                </span>
              </div>

              {/* Assigned To */}
              <div className="md:w-40">
                {record.assignedToBookTitle ? (
                  <div className="flex items-center gap-1">
                    <BookOpen className="h-3 w-3 text-muted-foreground" />
                    <span className="truncate text-xs">{record.assignedToBookTitle}</span>
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">Unassigned</span>
                )}
              </div>

              {/* Barcode */}
              <div className="md:w-28">
                <BarcodePreview
                  record={record}
                  onDownload={() => onDownloadBarcode(record.id)}
                />
              </div>

              {/* Status */}
              <div className="md:w-24">
                <StatusBadge status={record.status} />
              </div>

              {/* Actions */}
              <div className="flex-1">
                {record.status === "available" && (
                  <AssignISBNDropdown
                    record={record}
                    bookOptions={bookOptions}
                    onAssign={onAssignISBN}
                    isAssigning={isAssigning}
                  />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
