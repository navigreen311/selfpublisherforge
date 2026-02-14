"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useBooks } from "@/modules/writing/hooks";
import { useCreatePipeline } from "../hooks";
import { useTranslations } from "@/hooks/use-translations";
import type { PipelineTemplateName } from "../types";

const TEMPLATE_OPTIONS: {
  value: PipelineTemplateName;
  label: string;
  desc: string;
}[] = [
  {
    value: "nonfiction",
    label: "Nonfiction",
    desc: "Standard nonfiction publishing pipeline",
  },
  {
    value: "fiction",
    label: "Fiction",
    desc: "Full fiction book publishing pipeline",
  },
  {
    value: "short_story",
    label: "Short Story",
    desc: "Streamlined pipeline for short works",
  },
  {
    value: "series_launch",
    label: "Series Launch",
    desc: "Multi-book series launch coordination",
  },
  { value: "blank", label: "Blank", desc: "Start from scratch" },
];

interface CreatePipelineModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreatePipelineModal({
  open,
  onOpenChange,
}: CreatePipelineModalProps) {
  const t = useTranslations("pipeline");
  const createMutation = useCreatePipeline();
  const { data: books, isLoading: booksLoading } = useBooks();

  const [name, setName] = useState("");
  const [bookId, setBookId] = useState("");
  const [useManualBookId, setUseManualBookId] = useState(false);
  const [template, setTemplate] = useState<PipelineTemplateName>("blank");
  const [targetDate, setTargetDate] = useState("");
  const [deadline, setDeadline] = useState("");

  function resetForm() {
    setName("");
    setBookId("");
    setUseManualBookId(false);
    setTemplate("blank");
    setTargetDate("");
    setDeadline("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedName = name.trim();
    const trimmedBookId = bookId.trim();
    if (!trimmedName || !trimmedBookId) return;

    createMutation.mutate(
      {
        name: trimmedName,
        book_id: trimmedBookId,
        deadline: deadline || undefined,
        settings: {
          template: template,
          target_launch_date: targetDate || undefined,
        },
      },
      {
        onSuccess: () => {
          resetForm();
          onOpenChange(false);
        },
      }
    );
  }

  const isValid = name.trim().length >= 3 && bookId.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("newPipeline")}</DialogTitle>
          <DialogDescription>
            Create a new production pipeline for your book.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Pipeline name */}
          <div>
            <label
              htmlFor="modal-pl-name"
              className="block text-sm font-medium mb-1"
            >
              {t("pipelineName")}
            </label>
            <input
              id="modal-pl-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("pipelineNamePlaceholder")}
              className="w-full border rounded-md px-3 py-2 text-sm"
              required
              minLength={3}
              maxLength={100}
            />
          </div>

          {/* Book selection */}
          <div>
            <label
              htmlFor="modal-pl-book"
              className="block text-sm font-medium mb-1"
            >
              {t("book")}
            </label>
            {!useManualBookId && books && books.length > 0 ? (
              <>
                <select
                  id="modal-pl-book"
                  value={bookId}
                  onChange={(e) => setBookId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-card"
                  required
                >
                  <option value="">{t("selectBook")}</option>
                  {books.map((book) => (
                    <option key={book.id} value={book.id}>
                      {book.title}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => {
                    setUseManualBookId(true);
                    setBookId("");
                  }}
                  className="mt-1 text-xs text-blue-600 hover:underline"
                >
                  {t("enterBookIdManually")}
                </button>
              </>
            ) : (
              <>
                <input
                  id="modal-pl-book"
                  type="text"
                  value={bookId}
                  onChange={(e) => setBookId(e.target.value)}
                  placeholder={t("bookIdPlaceholder")}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  required
                />
                {booksLoading && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {t("loadingBooks")}
                  </p>
                )}
                {useManualBookId && books && books.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setUseManualBookId(false);
                      setBookId("");
                    }}
                    className="mt-1 text-xs text-blue-600 hover:underline"
                  >
                    {t("selectFromBooks")}
                  </button>
                )}
              </>
            )}
          </div>

          {/* Template selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Template</label>
            <div className="grid grid-cols-1 gap-2">
              {TEMPLATE_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-start gap-3 p-3 border rounded-md cursor-pointer transition-colors ${
                    template === opt.value
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <input
                    type="radio"
                    name="template"
                    value={opt.value}
                    checked={template === opt.value}
                    onChange={() => setTemplate(opt.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <p className="text-sm font-medium">{opt.label}</p>
                    <p className="text-xs text-muted-foreground">{opt.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="modal-pl-target"
                className="block text-sm font-medium mb-1"
              >
                Target Launch Date
              </label>
              <input
                id="modal-pl-target"
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label
                htmlFor="modal-pl-deadline"
                className="block text-sm font-medium mb-1"
              >
                Deadline
              </label>
              <input
                id="modal-pl-deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm"
              />
            </div>
          </div>

          <DialogFooter>
            <button
              type="button"
              onClick={() => {
                resetForm();
                onOpenChange(false);
              }}
              className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
            >
              {t("cancel")}
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !isValid}
              className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? t("creating") : t("create")}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
