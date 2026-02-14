"use client";

import { useState, useCallback } from "react";
import { format } from "date-fns";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { useProjects } from "@/modules/projects/hooks";
import { useCreateARCCampaign } from "../hooks";
import type { ARCRecipientAdd } from "../types";

interface ARCCampaignWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const STEPS = [
  "Campaign Info",
  "ARC File",
  "Recipients",
  "Deadline",
  "Confirm",
] as const;

export function ARCCampaignWizard({ open, onOpenChange }: ARCCampaignWizardProps) {
  const [step, setStep] = useState(0);
  const [campaignName, setCampaignName] = useState("");
  const [bookId, setBookId] = useState("");
  const [arcFileUrl, setArcFileUrl] = useState("");
  const [recipients, setRecipients] = useState<ARCRecipientAdd[]>([]);
  const [bulkInput, setBulkInput] = useState("");
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [deadline, setDeadline] = useState("");

  const { data: projects, isLoading: projectsLoading } = useProjects();
  const createCampaign = useCreateARCCampaign();

  const resetForm = useCallback(() => {
    setStep(0);
    setCampaignName("");
    setBookId("");
    setArcFileUrl("");
    setRecipients([]);
    setBulkInput("");
    setNewName("");
    setNewEmail("");
    setDeadline("");
  }, []);

  const handleOpenChange = useCallback(
    (value: boolean) => {
      if (!value) {
        resetForm();
      }
      onOpenChange(value);
    },
    [onOpenChange, resetForm]
  );

  const parseBulkEmails = useCallback(() => {
    if (!bulkInput.trim()) return;

    const lines = bulkInput
      .split(/[\n,;]+/)
      .map((line) => line.trim())
      .filter(Boolean);

    const parsed: ARCRecipientAdd[] = [];
    for (const line of lines) {
      // Try "Name <email>" format
      const angleMatch = line.match(/^(.+?)\s*<(.+?)>$/);
      if (angleMatch) {
        parsed.push({ name: angleMatch[1].trim(), email: angleMatch[2].trim() });
        continue;
      }
      // Just an email
      if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(line)) {
        parsed.push({ name: line.split("@")[0], email: line });
        continue;
      }
    }

    if (parsed.length > 0) {
      setRecipients((prev) => {
        const existingEmails = new Set(prev.map((r) => r.email.toLowerCase()));
        const newRecipients = parsed.filter(
          (r) => !existingEmails.has(r.email.toLowerCase())
        );
        return [...prev, ...newRecipients];
      });
      setBulkInput("");
      toast.success(`Added ${parsed.length} recipient(s)`);
    } else {
      toast.error("No valid emails found in input");
    }
  }, [bulkInput]);

  const addManualRecipient = useCallback(() => {
    if (!newName.trim() || !newEmail.trim()) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail.trim())) {
      toast.error("Invalid email address");
      return;
    }
    const exists = recipients.some(
      (r) => r.email.toLowerCase() === newEmail.trim().toLowerCase()
    );
    if (exists) {
      toast.error("Recipient already added");
      return;
    }
    setRecipients((prev) => [...prev, { name: newName.trim(), email: newEmail.trim() }]);
    setNewName("");
    setNewEmail("");
  }, [newName, newEmail, recipients]);

  const removeRecipient = useCallback((index: number) => {
    setRecipients((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleSubmit = useCallback(async () => {
    try {
      await createCampaign.mutateAsync({
        name: campaignName,
        book_id: bookId,
        description: arcFileUrl ? `ARC File: ${arcFileUrl}` : undefined,
        deadline: deadline || undefined,
        recipients: recipients as { name: string; email: string }[],
      });
      toast.success("ARC campaign created successfully");
      handleOpenChange(false);
    } catch {
      // Error handled by hook
    }
  }, [campaignName, bookId, arcFileUrl, deadline, recipients, createCampaign, handleOpenChange]);

  const canProceed = (): boolean => {
    switch (step) {
      case 0:
        return !!campaignName.trim() && !!bookId;
      case 1:
        return true; // ARC file URL is optional
      case 2:
        return recipients.length > 0;
      case 3:
        return true; // Deadline is optional
      case 4:
        return true;
      default:
        return false;
    }
  };

  const selectedBook = projects?.find((p) => p.id === bookId);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create ARC Campaign</DialogTitle>
          <DialogDescription>
            Step {step + 1} of {STEPS.length}: {STEPS[step]}
          </DialogDescription>
        </DialogHeader>

        {/* Step Progress */}
        <div className="flex gap-1">
          {STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`h-1 flex-1 rounded-full transition-colors ${
                idx <= step ? "bg-blue-600" : "bg-gray-200"
              }`}
            />
          ))}
        </div>

        {/* Step 1: Campaign Info */}
        {step === 0 && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="arc-campaign-name">Campaign Name</Label>
              <Input
                id="arc-campaign-name"
                placeholder="e.g., Spring Book Launch ARC"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="arc-book">Select Book</Label>
              {projectsLoading ? (
                <div className="h-10 bg-gray-100 rounded-md animate-pulse" />
              ) : (
                <Select value={bookId} onValueChange={setBookId}>
                  <SelectTrigger id="arc-book">
                    <SelectValue placeholder="Choose a book" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects && projects.length > 0 ? (
                      projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.title}
                        </SelectItem>
                      ))
                    ) : (
                      <SelectItem value="__none" disabled>
                        No books found
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>
        )}

        {/* Step 2: ARC File URL */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="arc-file-url">ARC File URL</Label>
              <Input
                id="arc-file-url"
                type="url"
                placeholder="https://drive.google.com/... or direct download link"
                value={arcFileUrl}
                onChange={(e) => setArcFileUrl(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Provide a link to your ARC file (Google Drive, Dropbox, BookFunnel, etc.). Optional.
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Recipients */}
        {step === 2 && (
          <div className="space-y-4">
            {/* Bulk entry */}
            <div className="space-y-1.5">
              <Label htmlFor="arc-bulk-emails">Bulk Add Recipients</Label>
              <Textarea
                id="arc-bulk-emails"
                placeholder={"Enter emails (one per line or comma-separated):\njohn@example.com\nJane Doe <jane@example.com>"}
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
                rows={4}
                className="text-sm"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={parseBulkEmails}
                disabled={!bulkInput.trim()}
              >
                Parse & Add
              </Button>
            </div>

            {/* Manual add */}
            <div className="space-y-1.5">
              <Label>Add Manually</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Email"
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={addManualRecipient}
                  disabled={!newName.trim() || !newEmail.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Recipient list */}
            {recipients.length > 0 && (
              <div className="space-y-1">
                <Label>Recipients ({recipients.length})</Label>
                <div className="max-h-40 overflow-y-auto space-y-1 border rounded-lg p-2">
                  {recipients.map((r, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-sm py-1 px-2 rounded hover:bg-muted"
                    >
                      <span>
                        <span className="font-medium">{r.name}</span>{" "}
                        <span className="text-muted-foreground">({r.email})</span>
                      </span>
                      <button
                        onClick={() => removeRecipient(idx)}
                        className="text-muted-foreground hover:text-destructive p-1"
                        aria-label={`Remove ${r.name}`}
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {recipients.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                Add at least one recipient to continue.
              </p>
            )}
          </div>
        )}

        {/* Step 4: Deadline */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="arc-deadline">Review Deadline</Label>
              <Input
                id="arc-deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                min={new Date().toISOString().split("T")[0]}
              />
              <p className="text-xs text-muted-foreground">
                Set a deadline for when you would like reviews submitted. Optional.
              </p>
            </div>
          </div>
        )}

        {/* Step 5: Summary */}
        {step === 4 && (
          <div className="space-y-4">
            <div className="bg-muted rounded-lg p-4 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Campaign:</span>
                <span className="font-medium">{campaignName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Book:</span>
                <span className="font-medium">{selectedBook?.title || bookId}</span>
              </div>
              {arcFileUrl && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ARC File:</span>
                  <span className="font-medium truncate max-w-[200px]">{arcFileUrl}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Recipients:</span>
                <span className="font-medium">{recipients.length}</span>
              </div>
              {deadline && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Deadline:</span>
                  <span className="font-medium">
                    {format(new Date(deadline + "T00:00:00"), "MMM d, yyyy")}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          {step > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep((s) => s - 1)}
            >
              Back
            </Button>
          )}
          {step < STEPS.length - 1 ? (
            <Button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              disabled={!canProceed()}
            >
              Next
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={createCampaign.isPending}
            >
              {createCampaign.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Campaign"
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
