"use client";

import { useState } from "react";
import { Plus, Puzzle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PuzzleBookList } from "@/modules/specialty-books/puzzles/components/PuzzleBookList";
import { TemplateCards } from "@/modules/specialty-books/puzzles/components/TemplateCards";
import { CreatePuzzleBookWizard } from "@/modules/specialty-books/puzzles/components/CreatePuzzleBookWizard";
import type { PuzzleTemplate } from "@/modules/specialty-books/puzzles/types";

export default function PuzzleBooksPage() {
  const [wizardOpen, setWizardOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<
    PuzzleTemplate | undefined
  >();

  const handleTemplateSelect = (template: PuzzleTemplate) => {
    setSelectedTemplate(template);
    setWizardOpen(true);
  };

  const handleCreateNew = () => {
    setSelectedTemplate(undefined);
    setWizardOpen(true);
  };

  return (
    <div className="container mx-auto py-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Puzzle className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Puzzle Book Generator</h1>
            <p className="text-muted-foreground">
              Create word search, crossword, maze, sudoku, and more puzzle books
            </p>
          </div>
        </div>
        <Button onClick={handleCreateNew}>
          <Plus className="h-4 w-4 mr-2" /> New Puzzle Book
        </Button>
      </div>

      {/* Template Cards */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Start from a Template</h2>
        <TemplateCards onSelect={handleTemplateSelect} />
      </div>

      {/* Book List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Puzzle Books</h2>
        <PuzzleBookList onCreateNew={handleCreateNew} />
      </div>

      {/* Wizard */}
      <CreatePuzzleBookWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        initialTemplate={selectedTemplate}
      />
    </div>
  );
}
