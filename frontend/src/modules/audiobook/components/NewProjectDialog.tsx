"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateAudiobookProject } from "../hooks";
import { useBooks } from "@/modules/writing/hooks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface NewProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TARGET_PLATFORMS = [
  { value: "acx", label: "ACX" },
  { value: "findaway", label: "Findaway Voices" },
  { value: "generic", label: "Generic" },
] as const;

const OUTPUT_FORMATS = [
  { value: "mp3", label: "MP3" },
  { value: "m4b", label: "M4B" },
  { value: "flac", label: "FLAC" },
  { value: "wav", label: "WAV" },
] as const;

const SAMPLE_RATES = [
  { value: "44100", label: "44,100 Hz" },
  { value: "48000", label: "48,000 Hz" },
] as const;

const BIT_RATES = [
  { value: "128", label: "128 kbps" },
  { value: "192", label: "192 kbps" },
  { value: "256", label: "256 kbps" },
  { value: "320", label: "320 kbps" },
] as const;

const CHANNELS = [
  { value: "1", label: "Mono" },
  { value: "2", label: "Stereo" },
] as const;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function NewProjectDialog({ open, onOpenChange }: NewProjectDialogProps) {
  const router = useRouter();
  const { data: books, isLoading: booksLoading } = useBooks();
  const { mutate: createProject, isPending } = useCreateAudiobookProject();

  // Form state
  const [bookId, setBookId] = useState("");
  const [title, setTitle] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("acx");
  const [outputFormat, setOutputFormat] = useState("mp3");
  const [sampleRate, setSampleRate] = useState("44100");
  const [bitRate, setBitRate] = useState("192");
  const [channels, setChannels] = useState("1");

  const resetForm = () => {
    setBookId("");
    setTitle("");
    setTargetPlatform("acx");
    setOutputFormat("mp3");
    setSampleRate("44100");
    setBitRate("192");
    setChannels("1");
  };

  const handleBookChange = (value: string) => {
    setBookId(value);
    // Auto-fill title from book title if title is empty
    if (!title) {
      const selectedBook = books?.find((b) => b.id === value);
      if (selectedBook) {
        setTitle(selectedBook.title);
      }
    }
  };

  const handleSubmit = () => {
    if (!bookId) {
      toast.error("Please select a book");
      return;
    }

    createProject(
      {
        book_id: bookId,
        title: title || undefined,
        target_platform: targetPlatform,
        output_format: outputFormat,
        sample_rate: Number(sampleRate),
        bit_rate: Number(bitRate),
        channels: Number(channels),
      },
      {
        onSuccess: (project) => {
          toast.success("Audiobook project created");
          resetForm();
          onOpenChange(false);
          router.push(`/audiobook-studio/${project.id}`);
        },
      },
    );
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen && !isPending) {
      resetForm();
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New Audiobook Project</DialogTitle>
          <DialogDescription>
            Configure your audiobook project settings and output preferences.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Book selector */}
          <div className="space-y-2">
            <Label htmlFor="npd-book">Book</Label>
            {booksLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading books...
              </div>
            ) : books && books.length > 0 ? (
              <Select value={bookId} onValueChange={handleBookChange}>
                <SelectTrigger id="npd-book">
                  <SelectValue placeholder="Select a book" />
                </SelectTrigger>
                <SelectContent>
                  {books.map((book) => (
                    <SelectItem key={book.id} value={book.id}>
                      {book.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                id="npd-book-id"
                placeholder="Enter book ID"
                value={bookId}
                onChange={(e) => setBookId(e.target.value)}
              />
            )}
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="npd-title">Title (optional)</Label>
            <Input
              id="npd-title"
              placeholder="Auto-fills from book title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Target platform */}
          <div className="space-y-2">
            <Label htmlFor="npd-platform">Target Platform</Label>
            <Select value={targetPlatform} onValueChange={setTargetPlatform}>
              <SelectTrigger id="npd-platform">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TARGET_PLATFORMS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Output format */}
          <div className="space-y-2">
            <Label htmlFor="npd-format">Output Format</Label>
            <Select value={outputFormat} onValueChange={setOutputFormat}>
              <SelectTrigger id="npd-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OUTPUT_FORMATS.map((f) => (
                  <SelectItem key={f.value} value={f.value}>
                    {f.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Audio settings row */}
          <div className="space-y-2">
            <Label>Audio Settings</Label>
            <div className="grid grid-cols-3 gap-3">
              {/* Sample rate */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Sample Rate</span>
                <Select value={sampleRate} onValueChange={setSampleRate}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SAMPLE_RATES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Bit rate */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Bit Rate</span>
                <Select value={bitRate} onValueChange={setBitRate}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BIT_RATES.map((b) => (
                      <SelectItem key={b.value} value={b.value}>
                        {b.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Channels */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Channels</span>
                <Select value={channels} onValueChange={setChannels}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((c) => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !bookId}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isPending ? "Creating..." : "Create Project"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
