"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Pencil,
  Check,
  Save,
  Clock,
  FileText,
  Printer,
  Target,
  Keyboard,
  History,
  Maximize,
  Settings,
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
const LEFT_PANEL_WIDTH = 240;
const RIGHT_PANEL_WIDTH = 320;
const PANEL_TRANSITION_MS = 300;

// ---------------------------------------------------------------------------
// Save Status Indicator
// ---------------------------------------------------------------------------

function SaveStatusIndicator({ status }: { status: SaveStatus }) {
  const t = useTranslations("writing");

  const config: Record<
    SaveStatus,
    { label: string; color: string; icon: React.ReactNode }
  > = {
    saved: {
      label: t("editor.saveStatus.saved"),
      color: "text-green-600 dark:text-green-400",
      icon: <Check className="h-3.5 w-3.5" />,
    },
    saving: {
      label: t("editor.saveStatus.saving"),
      color: "text-muted-foreground",
      icon: <Save className="h-3.5 w-3.5 animate-pulse" />,
    },
    unsaved: {
      label: t("editor.saveStatus.unsaved"),
      color: "text-orange-500 dark:text-orange-400",
      icon: <FileText className="h-3.5 w-3.5" />,
    },
    idle: {
      label: t("editor.saveStatus.saved"),
      color: "text-green-600 dark:text-green-400",
      icon: <Check className="h-3.5 w-3.5" />,
    },
    error: {
      label: t("editor.saveStatus.error"),
      color: "text-red-500 dark:text-red-400",
      icon: <FileText className="h-3.5 w-3.5" />,
    },
  };

  const { label, color, icon } = config[status] ?? config.idle;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-xs font-medium select-none",
        color,
      )}
    >
      {icon}
      {label}
    </span>
  );
}

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
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState("");
  const titleInputRef = useRef<HTMLInputElement>(null);

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
    activeChapterId || "",
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
    1500,
  );

  // ---- Sync title from manuscript ------------------------------------------
  useEffect(() => {
    if (manuscript?.title) setTitleValue(manuscript.title);
  }, [manuscript?.title]);

  // Auto-focus title input when editing
  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditingTitle]);

  // ---- Computed values -----------------------------------------------------
  const activeChapter = chapters.find((c) => c.id === activeChapterId);
  const isLoading = manuscriptLoading || chaptersLoading;

  // Word count from current editor content (plain text extraction)
  const currentWordCount = editorContent
    .replace(/<[^>]*>/g, " ")
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length;

  const readingTime = Math.max(
    1,
    Math.ceil(currentWordCount / WORDS_PER_MINUTE),
  );

  // Session duration in minutes
  const sessionMinutes = Math.floor(
    (Date.now() - sessionStartRef.current) / 60000,
  );
  const sessionWordsWritten = Math.max(
    0,
    currentWordCount - sessionStartWordsRef.current,
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
    [activeChapterId, chapters, editorContent, updateChapter],
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
      },
    );
  }, [chapters.length, createChapter, t]);

  /** Reorder chapters via drag-and-drop. */
  const handleReorderChapters = useCallback(
    (newOrder: { chapter_id: string; order: number }[]) => {
      reorderChapters.mutate(newOrder);
    },
    [reorderChapters],
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
    [activeChapterId, deleteChapter],
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
    [selectedText],
  );

  /** Manual save. */
  const handleSave = useCallback(() => {
    saveNow();
  }, [saveNow]);

  /** Commit the inline title edit. */
  const handleTitleSave = useCallback(() => {
    setIsEditingTitle(false);
    // TODO: persist title change via API
  }, []);

  /** Cancel the inline title edit. */
  const handleTitleCancel = useCallback(() => {
    setTitleValue(manuscript?.title || "");
    setIsEditingTitle(false);
  }, [manuscript?.title]);

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
    <div
      className={cn(
        "flex flex-col h-[calc(100vh-4rem)] -m-6",
        distractionFree && "fixed inset-0 z-50 h-screen m-0 bg-background",
      )}
    >
      {/* ================================================================= */}
      {/* TOP BAR                                                           */}
      {/* ================================================================= */}
      {!distractionFree && (
        <header className="flex items-center justify-between border-b bg-card px-4 py-2 flex-shrink-0">
          {/* Left: Back link + inline editable title */}
          <div className="flex items-center gap-3 min-w-0">
            <Link
              href="/writing"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">
                {t("editor.backToStudio")}
              </span>
            </Link>

            <span className="text-border select-none">|</span>

            {/* Inline editable title */}
            {isEditingTitle ? (
              <div className="flex items-center gap-1.5 min-w-0">
                <input
                  ref={titleInputRef}
                  type="text"
                  value={titleValue}
                  onChange={(e) => setTitleValue(e.target.value)}
                  onBlur={handleTitleSave}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleTitleSave();
                    }
                    if (e.key === "Escape") {
                      e.preventDefault();
                      handleTitleCancel();
                    }
                  }}
                  className="text-sm font-semibold bg-transparent border-b-2 border-primary outline-none max-w-md min-w-[120px] px-1 py-0.5"
                  aria-label={t("editor.titleEditable")}
                />
                <button
                  onClick={handleTitleSave}
                  className="text-primary hover:text-primary/80 transition-colors"
                  aria-label={t("editor.save")}
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <button
                className="group inline-flex items-center gap-1.5 min-w-0"
                onClick={() => setIsEditingTitle(true)}
                title={t("editor.titleEditable")}
              >
                <h1 className="text-sm font-semibold text-foreground truncate max-w-md group-hover:text-primary transition-colors">
                  {manuscript?.title || t("editor.untitled")}
                </h1>
                <Pencil className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </button>
            )}
          </div>

          {/* Right: Save status + action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Save status indicator */}
            <SaveStatusIndicator status={saveStatus} />

            {/* Save button */}
            <button
              onClick={handleSave}
              disabled={saveStatus === "saving"}
              className={cn(
                "inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded font-medium transition-colors disabled:opacity-50",
                "bg-primary text-primary-foreground hover:bg-primary/90",
              )}
            >
              <Save className="h-3.5 w-3.5" />
              {t("editor.save")}
            </button>

            {/* Export dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded border hover:bg-accent transition-colors"
                  aria-label={t("editor.export")}
                >
                  <Download className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{t("editor.export")}</span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {["docx", "epub", "pdf", "txt", "markdown"].map((fmt) => (
                  <DropdownMenuItem
                    key={fmt}
                    onSelect={() => handleExport(fmt)}
                  >
                    {t(`editor.exportMenu.${fmt}`)}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* More actions overflow menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="inline-flex items-center justify-center h-8 w-8 rounded border hover:bg-accent transition-colors"
                  aria-label={t("editor.overflowMenu.label")}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem
                  onSelect={() => setVersionHistoryOpen(true)}
                >
                  <History className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.versionHistory")}
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Target className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.wordCountGoals")}
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Printer className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.printPreview")}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={toggleDistractionFree}>
                  <Maximize className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.distractionFree")}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={() => setShortcutsOpen(true)}
                >
                  <Keyboard className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.keyboardShortcuts")}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Settings className="h-4 w-4 mr-2" />
                  {t("editor.overflowMenu.settings")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
      )}

      {/* ================================================================= */}
      {/* MAIN 3-COLUMN LAYOUT                                              */}
      {/* ================================================================= */}
      <div className="flex flex-1 min-h-0 relative overflow-hidden">
        {/* -------------------------------------------------------------- */}
        {/* LEFT PANEL: Chapter Sidebar (240px, collapsible)               */}
        {/* -------------------------------------------------------------- */}
        {!distractionFree && (
          <>
            <div
              className="flex-shrink-0 border-r bg-card overflow-hidden"
              style={{
                width: showChapterPanel ? `${LEFT_PANEL_WIDTH}px` : "0px",
                minWidth: showChapterPanel ? `${LEFT_PANEL_WIDTH}px` : "0px",
                transition: `width ${PANEL_TRANSITION_MS}ms ease-in-out, min-width ${PANEL_TRANSITION_MS}ms ease-in-out, opacity ${PANEL_TRANSITION_MS}ms ease-in-out`,
                opacity: showChapterPanel ? 1 : 0,
              }}
            >
              <ChapterSidebar
                chapters={chapters}
                activeChapterId={activeChapterId}
                onSelectChapter={handleSelectChapter}
                onCreateChapter={handleCreateChapter}
                onReorderChapters={handleReorderChapters}
                onDeleteChapter={handleDeleteChapter}
                className="w-full h-full"
              />
            </div>

            {/* Left panel toggle button */}
            <button
              onClick={toggleChapterPanel}
              className={cn(
                "absolute top-2 z-10 h-8 w-8 flex items-center justify-center",
                "rounded-md border bg-card shadow-sm",
                "hover:bg-accent transition-all",
                showChapterPanel
                  ? "left-[228px]"
                  : "left-2",
              )}
              style={{
                transition: `left ${PANEL_TRANSITION_MS}ms ease-in-out`,
              }}
              aria-label={
                showChapterPanel
                  ? t("editor.hideChapters")
                  : t("editor.showChapters")
              }
              title={
                showChapterPanel
                  ? "Hide chapters (Ctrl+Shift+C)"
                  : "Show chapters (Ctrl+Shift+C)"
              }
            >
              {showChapterPanel ? (
                <PanelLeftClose className="h-4 w-4" />
              ) : (
                <PanelLeftOpen className="h-4 w-4" />
              )}
            </button>
          </>
        )}

        {/* -------------------------------------------------------------- */}
        {/* CENTER PANEL: Editor (fluid width)                              */}
        {/* -------------------------------------------------------------- */}
        <div
          className="flex-1 flex flex-col min-w-0"
          style={{
            transition: `margin ${PANEL_TRANSITION_MS}ms ease-in-out`,
          }}
        >
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">
                  {t("editor.loading")}
                </p>
              </div>
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
              <div className="text-center space-y-4 max-w-md px-6">
                <div className="mx-auto h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h2 className="text-lg font-semibold text-foreground">
                  {t("editor.emptyState")}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {t("editor.emptyStateDescription")}
                </p>
                <button
                  onClick={handleCreateChapter}
                  className="text-sm px-5 py-2.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-medium"
                >
                  {t("editor.createFirstChapter")}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* -------------------------------------------------------------- */}
        {/* RIGHT PANEL: AI Assistant (320px, collapsible)                 */}
        {/* -------------------------------------------------------------- */}
        {!distractionFree && (
          <>
            <div
              className="flex-shrink-0 border-l bg-card overflow-hidden"
              style={{
                width: showAIPanel ? `${RIGHT_PANEL_WIDTH}px` : "0px",
                minWidth: showAIPanel ? `${RIGHT_PANEL_WIDTH}px` : "0px",
                transition: `width ${PANEL_TRANSITION_MS}ms ease-in-out, min-width ${PANEL_TRANSITION_MS}ms ease-in-out, opacity ${PANEL_TRANSITION_MS}ms ease-in-out`,
                opacity: showAIPanel ? 1 : 0,
              }}
            >
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
                        flesch_kincaid_grade:
                          chapterReadability.flesch_kincaid_grade,
                        flesch_reading_ease:
                          chapterReadability.flesch_reading_ease,
                        passive_voice_pct:
                          chapterReadability.passive_voice_pct,
                        avg_words_per_sentence:
                          chapterReadability.avg_words_per_sentence,
                      }
                    : undefined
                }
                wordCount={currentWordCount}
                targetWordCount={
                  activeChapter?.target_word_count ?? targetWordCount
                }
                className="w-full h-full"
              />
            </div>

            {/* Right panel toggle button */}
            <button
              onClick={toggleAIPanel}
              className={cn(
                "absolute top-2 z-10 h-8 w-8 flex items-center justify-center",
                "rounded-md border bg-card shadow-sm",
                "hover:bg-accent transition-all",
                showAIPanel
                  ? "right-[308px]"
                  : "right-2",
              )}
              style={{
                transition: `right ${PANEL_TRANSITION_MS}ms ease-in-out`,
              }}
              aria-label={
                showAIPanel
                  ? t("editor.hideAI")
                  : t("editor.showAI")
              }
              title={
                showAIPanel
                  ? "Hide AI assistant (Ctrl+Shift+A)"
                  : "Show AI assistant (Ctrl+Shift+A)"
              }
            >
              {showAIPanel ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
            </button>
          </>
        )}
      </div>

      {/* ================================================================= */}
      {/* BOTTOM BAR (StatusBar component)                                  */}
      {/* ================================================================= */}
      {!distractionFree && (
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
      )}

      {/* Distraction-free mode: minimal floating controls */}
      {distractionFree && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={toggleDistractionFree}
            className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-card border shadow-sm hover:bg-accent transition-colors"
            title="Exit distraction-free mode (F11)"
          >
            <Maximize className="h-3.5 w-3.5" />
            {t("editor.exitDistractionFree")}
          </button>
        </div>
      )}

      {/* Version History Modal */}
      {versionHistoryOpen && (
        <VersionHistoryModal
          isOpen={versionHistoryOpen}
          onClose={() => setVersionHistoryOpen(false)}
          bookId={bookId}
          chapterId={activeChapterId || ""}
          chapterTitle={activeChapter?.title || ""}
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
