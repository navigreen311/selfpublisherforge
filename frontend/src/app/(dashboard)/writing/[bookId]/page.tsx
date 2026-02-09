"use client";

import { useCallback, useState } from "react";
import { useParams } from "next/navigation";
import { ManuscriptEditor } from "@/modules/writing/components/editor";
import { ChapterSidebar } from "@/modules/writing/components/chapter-sidebar";
import { AIPanel } from "@/modules/writing/components/ai-panel";
import {
  useManuscript,
  useChapters,
  useCreateChapter,
  useUpdateChapter,
  useReorderChapters,
  useReadabilityScore,
  type ChapterContent,
} from "@/modules/writing/hooks";

/**
 * Manuscript editor page.
 *
 * Full-featured writing workspace with:
 * - Chapter sidebar (left) for navigation and reordering
 * - Main editor (center) for writing content
 * - AI assistant panel (right) for generation and editing
 * - Word count and readability metrics
 */
export default function ManuscriptEditorPage() {
  const params = useParams();
  const bookId = params.bookId as string;

  const [activeChapterId, setActiveChapterId] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [showAIPanel, setShowAIPanel] = useState(true);
  const [aiSuggestion, setAiSuggestion] = useState<string | undefined>();

  // Data queries
  const { data: manuscript, isLoading: manuscriptLoading } =
    useManuscript(bookId);
  const { data: chapters = [], isLoading: chaptersLoading } =
    useChapters(bookId);
  const { data: readability } = useReadabilityScore(bookId);

  // Mutations
  const createChapter = useCreateChapter(bookId);
  const updateChapter = useUpdateChapter(bookId, activeChapterId || "");
  const reorderChapters = useReorderChapters(bookId);

  // Select a chapter and load its content
  const handleSelectChapter = useCallback(
    (chapterId: string) => {
      // Auto-save current chapter
      if (activeChapterId && editorContent) {
        updateChapter.mutate({ content: editorContent });
      }

      setActiveChapterId(chapterId);
      const chapter = chapters.find((c) => c.id === chapterId);
      if (chapter) {
        setEditorContent(chapter.content);
      }
    },
    [activeChapterId, chapters, editorContent, updateChapter]
  );

  // Create a new chapter
  const handleCreateChapter = useCallback(() => {
    const order = chapters.length + 1;
    createChapter.mutate(
      {
        title: `Chapter ${order}`,
        content: "",
        order,
      },
      {
        onSuccess: (newChapter: ChapterContent) => {
          setActiveChapterId(newChapter.id);
          setEditorContent("");
        },
      }
    );
  }, [chapters.length, createChapter]);

  // Reorder chapters via drag and drop
  const handleReorderChapters = useCallback(
    (newOrder: { chapter_id: string; order: number }[]) => {
      reorderChapters.mutate(newOrder);
    },
    [reorderChapters]
  );

  // Editor content change
  const handleEditorChange = useCallback((content: string) => {
    setEditorContent(content);
  }, []);

  // Text selection in editor
  const handleSelectionChange = useCallback((text: string) => {
    setSelectedText(text);
  }, []);

  // Insert AI-generated text at cursor
  const handleInsertText = useCallback(
    (text: string) => {
      setEditorContent((prev) => prev + "\n\n" + text);
    },
    []
  );

  // Replace selected text with AI-generated text
  const handleReplaceSelection = useCallback(
    (text: string) => {
      if (selectedText) {
        setEditorContent((prev) => prev.replace(selectedText, text));
        setSelectedText("");
      }
    },
    [selectedText]
  );

  // Accept AI suggestion
  const handleAcceptSuggestion = useCallback(() => {
    if (aiSuggestion) {
      setEditorContent((prev) => prev + aiSuggestion);
      setAiSuggestion(undefined);
    }
  }, [aiSuggestion]);

  // Dismiss AI suggestion
  const handleDismissSuggestion = useCallback(() => {
    setAiSuggestion(undefined);
  }, []);

  // Auto-save on blur / interval
  const handleSave = useCallback(() => {
    if (activeChapterId && editorContent) {
      updateChapter.mutate({ content: editorContent });
    }
  }, [activeChapterId, editorContent, updateChapter]);

  const activeChapter = chapters.find((c) => c.id === activeChapterId);
  const isLoading = manuscriptLoading || chaptersLoading;

  return (
    <div className="flex h-[calc(100vh-8rem)] -m-6">
      {/* Chapter sidebar */}
      <ChapterSidebar
        chapters={chapters}
        activeChapterId={activeChapterId}
        onSelectChapter={handleSelectChapter}
        onCreateChapter={handleCreateChapter}
        onReorderChapters={handleReorderChapters}
        className="w-64 flex-shrink-0"
      />

      {/* Main editor area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Editor toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b bg-card">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-medium text-foreground truncate max-w-md">
              {activeChapter?.title || manuscript?.title || "Select a chapter"}
            </h2>
            {activeChapter && (
              <span className="text-xs text-muted-foreground">
                {activeChapter.word_count.toLocaleString()} words
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {readability && (
              <span className="text-xs text-muted-foreground">
                Reading level: {readability.reading_level} | Flesch:{" "}
                {readability.flesch_reading_ease}
              </span>
            )}
            <button
              onClick={handleSave}
              className="text-xs px-3 py-1 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Save
            </button>
            <button
              onClick={() => setShowAIPanel(!showAIPanel)}
              className="text-xs px-3 py-1 rounded border hover:bg-accent transition-colors"
            >
              {showAIPanel ? "Hide AI" : "Show AI"}
            </button>
          </div>
        </div>

        {/* Editor */}
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-muted-foreground">Loading manuscript...</p>
          </div>
        ) : activeChapterId ? (
          <ManuscriptEditor
            content={editorContent}
            onChange={handleEditorChange}
            onSelectionChange={handleSelectionChange}
            aiSuggestion={aiSuggestion}
            onAcceptSuggestion={handleAcceptSuggestion}
            onDismissSuggestion={handleDismissSuggestion}
            className="flex-1"
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <p className="text-muted-foreground">
                Select a chapter from the sidebar to start editing,
                <br />
                or create a new chapter.
              </p>
              <button
                onClick={handleCreateChapter}
                className="text-sm px-4 py-2 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Create First Chapter
              </button>
            </div>
          </div>
        )}

        {/* Readability bar */}
        {readability && (
          <div className="flex items-center gap-6 px-4 py-1.5 border-t bg-muted/30 text-xs text-muted-foreground">
            <span>FK Grade: {readability.flesch_kincaid_grade}</span>
            <span>Fog: {readability.gunning_fog}</span>
            <span>SMOG: {readability.smog_index}</span>
            <span>
              Total: {manuscript?.total_word_count?.toLocaleString() || 0} words
            </span>
          </div>
        )}
      </div>

      {/* AI Panel */}
      {showAIPanel && (
        <AIPanel
          bookId={bookId}
          projectId={bookId}
          selectedText={selectedText}
          onInsertText={handleInsertText}
          onReplaceSelection={handleReplaceSelection}
        />
      )}
    </div>
  );
}
