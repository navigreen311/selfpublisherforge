"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  MoreHorizontal,
} from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

// New writing-studio components
import { ChapterSidebar } from "@/components/writing-studio/ChapterSidebar";
import { ManuscriptEditor } from "@/components/writing-studio/ManuscriptEditor";
import { AIAssistantPanel } from "@/components/writing-studio/AIAssistantPanel";
import { StatusBar } from "@/components/writing-studio/StatusBar";
import { VersionHistoryModal } from "@/components/writing-studio/VersionHistoryModal";
import { KeyboardShortcutsModal } from "@/components/writing-studio/KeyboardShortcutsModal";

// Data hooks
import {
  useManuscript,
  useChapters,
  useCreateChapter,
  useUpdateChapter,
  useReorderChapters,
  useDeleteChapter,
  useChapterReadability,
  useAutoSave,
  type ChapterContent,
  type SaveStatus,
} from "@/modules/writing/hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WORDS_PER_MINUTE = 250;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ManuscriptEditorPage() {
  const t = useTranslations("writing");
  const params = useParams();
  const rawBookId = params.bookId;
  const bookId =
    typeof rawBookId === "string"
      ? rawBookId
      : Array.isArray(rawBookId)
        ? rawBookId[0] ?? ""
        : "";

  // ---- State ---------------------------------------------------------------
  const [activeChapterId, setActiveChapterId] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [showAIPanel, setShowAIPanel] = useState(true);
  const [distractionFree, setDistractionFree] = useState(false);

  // Inline editable title
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState("");

  // Modal state
  const [versionHistoryOpen, setVersionHistoryOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  // Chapter panel toggle
  const [showChapterPanel, setShowChapterPanel] = useState(true);

  // Track session start time and starting word count for session stats
  const sessionStartRef = useRef(Date.now());
  const sessionStartWordsRef = useRef(0);

  // ---- Data queries --------------------------------------------------------
  const { data: manuscript, isLoading: manuscriptLoading } =
    useManuscript(bookId);
  const { data: chapters = [], isLoading: chaptersLoading } =
    useChapters(bookId);
  const { data: chapterReadability } = useChapterReadability(
    activeChapterId || ""
  );

  // ---- Mutations -----------------------------------------------------------
  const createChapter = useCreateChapter(bookId);
  const updateChapter = useUpdateChapter(bookId, activeChapterId || "");
  const reorderChapters = useReorderChapters(bookId);
  const deleteChapter = useDeleteChapter(bookId);

  // ---- Auto-save -----------------------------------------------------------
  const { saveStatus, saveNow } = useAutoSave(
    bookId,
    activeChapterId,
    editorContent,
    1500
  );

  // ---- Sync title from manuscript ------------------------------------------
  useEffect(() => {
    if (manuscript?.title) setTitleValue(manuscript.title);
  }, [manuscript?.title]);

  // ---- Computed values -----------------------------------------------------
  const activeChapter = chapters.find((c) => c.id === activeChapterId);
  const isLoading = manuscriptLoading || chaptersLoading;

  // Word count from current editor content (plain text extraction)
  const currentWordCount = editorContent
    .replace(/<[^>]*>/g, " ")
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length;

  const readingTime = Math.max(1, Math.ceil(currentWordCount / WORDS_PER_MINUTE));

  // Session duration in minutes
  const sessionMinutes = Math.floor(
    (Date.now() - sessionStartRef.current) / 60000
  );
  const sessionWordsWritten = Math.max(
    0,
    currentWordCount - sessionStartWordsRef.current
  );

  // Total manuscript word count
  const totalWordCount = manuscript?.total_word_count ?? 0;
  const targetWordCount = manuscript?.target_word_count ?? 0;

  // ---- Handlers ------------------------------------------------------------

  /** Select a chapter: save current first, then load the new one. */
  const handleSelectChapter = useCallback(
    (chapterId: string) => {
      // Save current chapter before switching
      if (activeChapterId && editorContent) {
        updateChapter.mutate({ content: editorContent });
      }

      setActiveChapterId(chapterId);
      const chapter = chapters.find((c) => c.id === chapterId);
      if (chapter) {
        setEditorContent(chapter.content);
        // Reset session word tracking for the new chapter
        sessionStartWordsRef.current = chapter.content
          .replace(/<[^>]*>/g, " ")
          .trim()
          .split(/\s+/)
          .filter((w) => w.length > 0).length;
      }
    },
    [activeChapterId, chapters, editorContent, updateChapter]
  );

  /** Create a new chapter. */
  const handleCreateChapter = useCallback(() => {
    const order = chapters.length + 1;
    createChapter.mutate(
      {
        title: t("editor.chapter", { number: order }),
        content: "",
        order,
      },
      {
        onSuccess: (newChapter: ChapterContent) => {
          setActiveChapterId(newChapter.id);
          setEditorContent("");
          sessionStartWordsRef.current = 0;
        },
      }
    );
  }, [chapters.length, createChapter, t]);

  /** Reorder chapters via drag-and-drop. */
  const handleReorderChapters = useCallback(
    (newOrder: { chapter_id: string; order: number }[]) => {
      reorderChapters.mutate(newOrder);
    },
    [reorderChapters]
  );

  /** Delete a chapter. */
  const handleDeleteChapter = useCallback(
    (chapterId: string) => {
      deleteChapter.mutate(chapterId, {
        onSuccess: () => {
          if (activeChapterId === chapterId) {
            setActiveChapterId(null);
            setEditorContent("");
          }
        },
      });
    },
    [activeChapterId, deleteChapter]
  );

  /** Editor content change (TipTap HTML). */
  const handleEditorChange = useCallback((html: string) => {
    setEditorContent(html);
  }, []);

  /** Text selection in the editor. */
  const handleSelectionChange = useCallback((text: string) => {
    setSelectedText(text);
  }, []);

  /** Insert AI-generated text at cursor. */
  const handleInsertText = useCallback((text: string) => {
    setEditorContent((prev) => prev + text);
  }, []);

  /** Replace selected text with AI-generated text. */
  const handleReplaceSelection = useCallback(
    (text: string) => {
      if (selectedText) {
        setEditorContent((prev) => prev.replace(selectedText, text));
        setSelectedText("");
      }
    },
    [selectedText]
  );

  /** Manual save. */
  const handleSave = useCallback(() => {
    saveNow();
  }, [saveNow]);

  /** Toggle distraction-free mode. */
  const toggleDistractionFree = useCallback(() => {
    setDistractionFree((prev) => !prev);
  }, []);

  /** Toggle AI panel. */
  const toggleAIPanel = useCallback(() => {
    setShowAIPanel((prev) => !prev);
  }, []);

  /** Toggle chapter panel. */
  const toggleChapterPanel = useCallback(() => {
    setShowChapterPanel((prev) => !prev);
  }, []);

  /** Export handler (stub). */
  const handleExport = useCallback((format: string) => {
    // Stub - would call export API
    console.log(`Exporting as ${format}`);
  }, []);

  // ---- Keyboard shortcuts --------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S: save
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        saveNow();
      }
      // Ctrl+Shift+A: toggle AI panel
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "A") {
        e.preventDefault();
        setShowAIPanel((prev) => !prev);
      }
      // Ctrl+Shift+C: toggle chapter panel
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "C") {
        e.preventDefault();
        setShowChapterPanel((prev) => !prev);
      }
      // F11: toggle distraction-free mode
      if (e.key === "F11") {
        e.preventDefault();
        setDistractionFree((prev) => !prev);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [saveNow]);

  // ---- Guard: invalid book ID ---------------------------------------------
  if (!bookId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">{t("editor.invalidBookId")}</p>
      </div>
    );
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-6">
      {/* ================================================================= */}
      {/* TOP BAR                                                           */}
      {/* ================================================================= */}
      <div className="flex items-center justify-between border-b bg-card px-4 py-2 flex-shrink-0">
        {/* Left: Back link + inline editable title */}
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/writing"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t("editor.backToStudio")}
          </Link>
          <span className="text-border">|</span>
          {editingTitle ? (
            <input
              type="text"
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={() => {
                setEditingTitle(false);
                // Save title change
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setEditingTitle(false);
                }
                if (e.key === "Escape") {
                  setTitleValue(manuscript?.title || "");
                  setEditingTitle(false);
                }
              }}
              className="text-sm font-semibold bg-transparent border-b border-primary outline-none max-w-md"
              autoFocus
            />
          ) : (
            <h1
              className="text-sm font-semibold text-foreground truncate max-w-md cursor-pointer hover:text-primary transition-colors"
              onClick={() => setEditingTitle(true)}
              title={t("editor.titleEditable")}
            >
              {manuscript?.title || t("editor.untitled")}
            </h1>
          )}
        </div>

        {/* Right: Save status + action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={saveStatus === "saving"}
            className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {t("editor.save")}
          </button>

          {/* Export dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded border hover:bg-accent transition-colors">
                <Download className="h-3.5 w-3.5" />
                {t("editor.export")}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {["docx", "epub", "pdf", "txt", "markdown"].map((fmt) => (
                <DropdownMenuItem key={fmt} onSelect={() => handleExport(fmt)}>
                  {t(`editor.exportMenu.${fmt}`)}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* More actions overflow menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="inline-flex items-center justify-center h-8 w-8 rounded border hover:bg-accent transition-colors">
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuItem onSelect={() => setVersionHistoryOpen(true)}>
                {t("editor.overflowMenu.versionHistory")}
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => setShortcutsOpen(true)}>
                {t("editor.overflowMenu.keyboardShortcuts")}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={toggleDistractionFree}>
                {t("editor.overflowMenu.distractionFree")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* ================================================================= */}
      {/* MAIN 3-COLUMN LAYOUT                                              */}
      {/* ================================================================= */}
      <div className="flex flex-1 min-h-0">
        {/* -------------------------------------------------------------- */}
        {/* LEFT PANEL: Chapter Sidebar                                     */}
        {/* -------------------------------------------------------------- */}
        {showChapterPanel && !distractionFree && (
          <ChapterSidebar
            chapters={chapters}
            activeChapterId={activeChapterId}
            onSelectChapter={handleSelectChapter}
            onCreateChapter={handleCreateChapter}
            onReorderChapters={handleReorderChapters}
            onDeleteChapter={handleDeleteChapter}
            className="w-64 flex-shrink-0"
          />
        )}

        {/* -------------------------------------------------------------- */}
        {/* CENTER PANEL: Editor                                            */}
        {/* -------------------------------------------------------------- */}
        <div className="flex-1 flex flex-col min-w-0">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-muted-foreground">{t("editor.loading")}</p>
            </div>
          ) : activeChapterId ? (
            <ManuscriptEditor
              content={editorContent}
              onChange={handleEditorChange}
              onSelectionChange={handleSelectionChange}
              onSave={handleSave}
              className="flex-1"
            />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-3">
                <p className="text-muted-foreground">
                  {t("editor.emptyState")}
                </p>
                <button
                  onClick={handleCreateChapter}
                  className="text-sm px-4 py-2 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  {t("editor.createFirstChapter")}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* -------------------------------------------------------------- */}
        {/* RIGHT PANEL: AI Assistant                                       */}
        {/* -------------------------------------------------------------- */}
        {showAIPanel && !distractionFree && (
          <AIAssistantPanel
            bookId={bookId}
            projectId={bookId}
            chapterId={activeChapterId || undefined}
            selectedText={selectedText}
            onInsertText={handleInsertText}
            onReplaceSelection={handleReplaceSelection}
            readabilityScore={
              chapterReadability
                ? {
                    flesch_kincaid_grade: chapterReadability.flesch_kincaid_grade,
                    flesch_reading_ease: chapterReadability.flesch_reading_ease,
                    passive_voice_pct: chapterReadability.passive_voice_pct,
                    avg_words_per_sentence:
                      chapterReadability.avg_words_per_sentence,
                  }
                : undefined
            }
            wordCount={currentWordCount}
            targetWordCount={activeChapter?.target_word_count ?? targetWordCount}
          />
        )}
      </div>

      {/* ================================================================= */}
      {/* BOTTOM BAR (StatusBar component)                                  */}
      {/* ================================================================= */}
      <StatusBar
        wordCount={currentWordCount}
        readingTime={readingTime}
        saveStatus={saveStatus}
        sessionWords={sessionWordsWritten}
        sessionMinutes={sessionMinutes}
        totalWordCount={totalWordCount}
        targetWordCount={targetWordCount}
        showAIPanel={showAIPanel}
        distractionFree={distractionFree}
        onToggleAIPanel={toggleAIPanel}
        onToggleDistractionFree={toggleDistractionFree}
      />

      {/* Version History Modal */}
      {versionHistoryOpen && (
        <VersionHistoryModal
          bookId={bookId}
          chapterId={activeChapterId || ""}
          open={versionHistoryOpen}
          onOpenChange={setVersionHistoryOpen}
          onRestore={(content) => {
            setEditorContent(content);
          }}
        />
      )}

      {/* Keyboard Shortcuts Modal */}
      {shortcutsOpen && (
        <KeyboardShortcutsModal
          open={shortcutsOpen}
          onOpenChange={setShortcutsOpen}
        />
      )}
    </div>
  );
}
