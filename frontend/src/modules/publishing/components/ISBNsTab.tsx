"use client";

import { useState, useCallback, useMemo } from "react";
import { Plus, Barcode, Download, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ISBNFormat = "Print" | "Ebook" | "Audiobook";
type ISBNStatus = "Available" | "In Use" | "Retired";

interface ISBN {
  id: string;
  isbn: string;
  format: ISBNFormat;
  assignedTo: string | null;
  status: ISBNStatus;
}

// ---------------------------------------------------------------------------
// Placeholder hook — will be replaced with a real API hook later
// ---------------------------------------------------------------------------

function useISBNs() {
  const [isbns, setISBNs] = useState<ISBN[]>([]);

  const addISBN = useCallback(
    (entry: Omit<ISBN, "id" | "status">) => {
      const newISBN: ISBN = {
        ...entry,
        id: crypto.randomUUID(),
        status: entry.assignedTo ? "In Use" : "Available",
      };
      setISBNs((prev) => [...prev, newISBN]);
    },
    [],
  );

  const retireISBN = useCallback((id: string) => {
    setISBNs((prev) =>
      prev.map((isbn) =>
        isbn.id === id ? { ...isbn, status: "Retired" as const } : isbn,
      ),
    );
  }, []);

  return { isbns, addISBN, retireISBN };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ISBN_FORMATS: ISBNFormat[] = ["Print", "Ebook", "Audiobook"];

/** Validates that the value is exactly 13 digits. */
function isValidISBN13(value: string): boolean {
  return /^\d{13}$/.test(value);
}

const STATUS_VARIANT: Record<ISBNStatus, "default" | "secondary" | "destructive"> = {
  Available: "default",
  "In Use": "secondary",
  Retired: "destructive",
};

// Placeholder book list for the assignment dropdown
const SAMPLE_BOOKS = [
  { id: "book-1", title: "Untitled Book 1" },
  { id: "book-2", title: "Untitled Book 2" },
  { id: "book-3", title: "Untitled Book 3" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ISBNsTab() {
  const { isbns, addISBN, retireISBN } = useISBNs();

  // Add-ISBN dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newIsbn, setNewIsbn] = useState("");
  const [newFormat, setNewFormat] = useState<ISBNFormat>("Print");
  const [newAssignment, setNewAssignment] = useState<string>("");
  const [isbnError, setIsbnError] = useState("");

  // Barcode generator state
  const [barcodeIsbn, setBarcodeIsbn] = useState<string>("");
  const [barcodePrice, setBarcodePrice] = useState("");

  const unassignedCount = useMemo(
    () => isbns.filter((i) => i.status === "Available").length,
    [isbns],
  );

  // ------ handlers ------

  const resetDialog = () => {
    setNewIsbn("");
    setNewFormat("Print");
    setNewAssignment("");
    setIsbnError("");
  };

  const handleAddISBN = () => {
    if (!isValidISBN13(newIsbn)) {
      setIsbnError("ISBN must be exactly 13 digits");
      return;
    }

    if (isbns.some((i) => i.isbn === newIsbn)) {
      setIsbnError("This ISBN has already been added");
      return;
    }

    addISBN({
      isbn: newIsbn,
      format: newFormat,
      assignedTo: newAssignment || null,
    });

    toast.success("ISBN added successfully");
    resetDialog();
    setDialogOpen(false);
  };

  const handleGenerateBarcode = () => {
    if (!barcodeIsbn) {
      toast.error("Please select an ISBN first");
      return;
    }
    toast.success("Barcode generated (placeholder)");
  };

  // ------ render ------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            ISBN Management
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage ISBNs across your books and formats.
          </p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetDialog(); }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add ISBN
            </Button>
          </DialogTrigger>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add ISBN</DialogTitle>
              <DialogDescription>
                Enter a 13-digit ISBN, choose a format, and optionally assign it
                to a book.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              {/* ISBN input */}
              <div className="space-y-2">
                <Label htmlFor="isbn-input">ISBN (13 digits)</Label>
                <Input
                  id="isbn-input"
                  placeholder="9781234567890"
                  maxLength={13}
                  value={newIsbn}
                  onChange={(e) => {
                    const digits = e.target.value.replace(/\D/g, "");
                    setNewIsbn(digits);
                    if (isbnError) setIsbnError("");
                  }}
                  error={isbnError || undefined}
                />
              </div>

              {/* Format dropdown */}
              <div className="space-y-2">
                <Label>Format</Label>
                <Select
                  value={newFormat}
                  onValueChange={(v) => setNewFormat(v as ISBNFormat)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select format" />
                  </SelectTrigger>
                  <SelectContent>
                    {ISBN_FORMATS.map((f) => (
                      <SelectItem key={f} value={f}>
                        {f}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Book assignment dropdown (optional) */}
              <div className="space-y-2">
                <Label>Assign to Book (optional)</Label>
                <Select
                  value={newAssignment}
                  onValueChange={setNewAssignment}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="None" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {SAMPLE_BOOKS.map((book) => (
                      <SelectItem key={book.id} value={book.title}>
                        {book.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => { resetDialog(); setDialogOpen(false); }}>
                Cancel
              </Button>
              <Button onClick={handleAddISBN}>Add ISBN</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Unassigned count info */}
      <div className="flex items-center gap-2 rounded-lg border bg-muted/40 px-4 py-3 text-sm">
        <Info className="h-4 w-4 text-muted-foreground" />
        <span>
          You have{" "}
          <span className="font-semibold">{unassignedCount}</span>{" "}
          unassigned ISBN{unassignedCount !== 1 ? "s" : ""}.
        </span>
      </div>

      {/* ISBN Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">ISBNs</CardTitle>
          <CardDescription>
            {isbns.length === 0
              ? 'No ISBNs registered yet. Click "Add ISBN" to get started.'
              : `${isbns.length} ISBN${isbns.length !== 1 ? "s" : ""} registered.`}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isbns.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ISBN</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Assigned To</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isbns.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-mono text-sm">
                      {entry.isbn}
                    </TableCell>
                    <TableCell>{entry.format}</TableCell>
                    <TableCell>
                      {entry.assignedTo ?? (
                        <span className="text-muted-foreground">Unassigned</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[entry.status]}>
                        {entry.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {entry.status !== "Retired" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => retireISBN(entry.id)}
                        >
                          Retire
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
              <p className="text-sm text-muted-foreground">
                No ISBNs to display.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Barcode Generator */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Barcode className="h-5 w-5" />
            Barcode Generator
          </CardTitle>
          <CardDescription>
            Generate a barcode image for any registered ISBN.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            {/* ISBN selection */}
            <div className="space-y-2">
              <Label>ISBN</Label>
              <Select value={barcodeIsbn} onValueChange={setBarcodeIsbn}>
                <SelectTrigger>
                  <SelectValue placeholder="Select ISBN" />
                </SelectTrigger>
                <SelectContent>
                  {isbns.length === 0 ? (
                    <SelectItem value="__empty__" disabled>
                      No ISBNs available
                    </SelectItem>
                  ) : (
                    isbns.map((entry) => (
                      <SelectItem key={entry.id} value={entry.isbn}>
                        {entry.isbn} ({entry.format})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Price input */}
            <div className="space-y-2">
              <Label htmlFor="barcode-price">Price</Label>
              <Input
                id="barcode-price"
                type="number"
                min={0}
                step={0.01}
                placeholder="9.99"
                value={barcodePrice}
                onChange={(e) => setBarcodePrice(e.target.value)}
              />
            </div>

            {/* Generate button */}
            <div className="flex items-end">
              <Button onClick={handleGenerateBarcode} className="w-full">
                Generate Barcode
              </Button>
            </div>
          </div>

          {/* Download buttons (placeholder) */}
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!barcodeIsbn}
              onClick={() => toast.info("PNG download coming soon")}
            >
              <Download className="mr-2 h-4 w-4" />
              Download PNG
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!barcodeIsbn}
              onClick={() => toast.info("SVG download coming soon")}
            >
              <Download className="mr-2 h-4 w-4" />
              Download SVG
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
