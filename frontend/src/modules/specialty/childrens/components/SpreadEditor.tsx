"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { PageThumbnailStrip, type PageData } from "./PageThumbnailStrip";
import { SpreadView, type ZoomLevel } from "./SpreadView";
import {
  PageProperties,
  type AgeRange,
  type TextProperties,
  type IllustrationProperties,
  type ReadabilityInfo,
} from "./PageProperties";
import type { LayoutType } from "./LayoutSelector";

// ─── Helper: generate a default page ────────────────────────────────────────

function createDefaultPage(pageNumber: number): PageData {
  return {
    id: `page-${Date.now()}-${pageNumber}`,
    pageNumber,
    layout: "top-image-bottom-text",
    textContent: "",
    illustrationUrl: undefined,
  };
}

function generateInitialPages(count: number): PageData[] {
  return Array.from({ length: count }, (_, i) => createDefaultPage(i + 1));
}

// ─── SpreadEditor Props ─────────────────────────────────────────────────────

interface SpreadEditorProps {
  /** Book's age range — drives minimum font size enforcement */
  ageRange?: AgeRange;
  /** Initial page count (default 32 for picture books) */
  initialPageCount?: number;
  /** Callback when pages change */
  onPagesChange?: (pages: PageData[]) => void;
  /** Class name for the outer container */
  className?: string;
}

// ─── SpreadEditor Component ─────────────────────────────────────────────────

export function SpreadEditor({
  ageRange = "picture",
  initialPageCount = 32,
  onPagesChange,
  className,
}: SpreadEditorProps) {
  // ── Core state ──────────────────────────────────────────────────────────
  const [pages, setPages] = React.useState<PageData[]>(() =>
    generateInitialPages(initialPageCount)
  );
  const [selectedPageIndex, setSelectedPageIndex] = React.useState(0);
  const [zoom, setZoom] = React.useState<ZoomLevel>(100);
  const [guidesVisible, setGuidesVisible] = React.useState(false);

  // ── Per-page property state ─────────────────────────────────────────────
  // In production these would be part of the page model; we keep them separate
  // so the editor can manage them independently.
  const [layoutMap, setLayoutMap] = React.useState<Record<string, LayoutType>>(
    {}
  );
  const [textPropsMap, setTextPropsMap] = React.useState<
    Record<string, TextProperties>
  >({});
  const [illustrationPropsMap, setIllustrationPropsMap] = React.useState<
    Record<string, IllustrationProperties>
  >({});

  // ── Derived state ───────────────────────────────────────────────────────
  const selectedPage = pages[selectedPageIndex] ?? null;

  const currentLayout: LayoutType =
    selectedPage
      ? layoutMap[selectedPage.id] ?? selectedPage.layout
      : "top-image-bottom-text";

  const currentTextProps: TextProperties = selectedPage
    ? textPropsMap[selectedPage.id] ?? {
        fontFamily: "Nunito",
        fontSize: 18,
        color: "#1a1a1a",
        position: "bottom" as const,
        autoTextPlate: false,
      }
    : {
        fontFamily: "Nunito",
        fontSize: 18,
        color: "#1a1a1a",
        position: "bottom" as const,
        autoTextPlate: false,
      };

  const currentIllustrationProps: IllustrationProperties = selectedPage
    ? illustrationPropsMap[selectedPage.id] ?? {
        prompt: "",
        trademarkSafe: null,
        characterConsistency: true,
      }
    : {
        prompt: "",
        trademarkSafe: null,
        characterConsistency: true,
      };

  // Simulated readability (would be computed from real content)
  const currentReadability: ReadabilityInfo = React.useMemo(() => {
    const ratio = 4.5 + Math.random() * 10;
    return {
      contrastScore: Math.round(ratio * 10) / 10,
      contrastPass: ratio >= 4.5,
      gutterSafe: true,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPage?.id]);

  // ── Spread computation ──────────────────────────────────────────────────
  // Show the selected page and its spread partner:
  //   - Even-indexed pages (0-based) show as left page
  //   - Odd-indexed pages show as right page
  const spreadLeftIndex =
    selectedPageIndex % 2 === 0 ? selectedPageIndex : selectedPageIndex - 1;
  const spreadRightIndex = spreadLeftIndex + 1;

  const leftPage = pages[spreadLeftIndex] ?? null;
  const rightPage = pages[spreadRightIndex] ?? null;

  // Apply layout overrides to spread pages for rendering
  const leftPageWithLayout = leftPage
    ? { ...leftPage, layout: layoutMap[leftPage.id] ?? leftPage.layout }
    : null;
  const rightPageWithLayout = rightPage
    ? { ...rightPage, layout: layoutMap[rightPage.id] ?? rightPage.layout }
    : null;

  // ── Callbacks ───────────────────────────────────────────────────────────

  const updatePages = React.useCallback(
    (newPages: PageData[]) => {
      setPages(newPages);
      onPagesChange?.(newPages);
    },
    [onPagesChange]
  );

  const handleAddPage = React.useCallback(() => {
    const newPage = createDefaultPage(pages.length + 1);
    updatePages([...pages, newPage]);
    setSelectedPageIndex(pages.length); // Select the new page
  }, [pages, updatePages]);

  const handleDeletePage = React.useCallback(
    (index: number) => {
      if (pages.length <= 1) return;
      const newPages = pages
        .filter((_, i) => i !== index)
        .map((page, i) => ({ ...page, pageNumber: i + 1 }));
      updatePages(newPages);

      // Adjust selection
      if (index >= newPages.length) {
        setSelectedPageIndex(newPages.length - 1);
      } else if (index < selectedPageIndex) {
        setSelectedPageIndex(selectedPageIndex - 1);
      }
    },
    [pages, selectedPageIndex, updatePages]
  );

  const handleReorderPages = React.useCallback(
    (reordered: PageData[]) => {
      updatePages(reordered);
    },
    [updatePages]
  );

  const handleLayoutChange = React.useCallback(
    (layout: LayoutType) => {
      if (!selectedPage) return;
      setLayoutMap((prev) => ({ ...prev, [selectedPage.id]: layout }));
      // Also update the page data
      const newPages = pages.map((p) =>
        p.id === selectedPage.id ? { ...p, layout } : p
      );
      updatePages(newPages);
    },
    [selectedPage, pages, updatePages]
  );

  const handleTextPropsChange = React.useCallback(
    (props: TextProperties) => {
      if (!selectedPage) return;
      setTextPropsMap((prev) => ({ ...prev, [selectedPage.id]: props }));
    },
    [selectedPage]
  );

  const handleIllustrationPropsChange = React.useCallback(
    (props: IllustrationProperties) => {
      if (!selectedPage) return;
      setIllustrationPropsMap((prev) => ({
        ...prev,
        [selectedPage.id]: props,
      }));
    },
    [selectedPage]
  );

  // Illustration action stubs (would call API in production)
  const handleGenerateIllustration = React.useCallback(() => {
    // TODO: Call /api/v1/specialty/childrens-books/{id}/pages/{page_id}/generate-illustration
    console.log("Generate illustration for page", selectedPage?.pageNumber);
  }, [selectedPage]);

  const handleUploadImage = React.useCallback(() => {
    // TODO: Open file picker and call upload endpoint
    console.log("Upload image for page", selectedPage?.pageNumber);
  }, [selectedPage]);

  const handleRegenerate = React.useCallback(() => {
    // TODO: Call generate-illustration with same prompt
    console.log("Regenerate illustration for page", selectedPage?.pageNumber);
  }, [selectedPage]);

  const handleGenerateVariations = React.useCallback(() => {
    // TODO: Call /api/v1/specialty/childrens-books/{id}/pages/{page_id}/generate-variations
    console.log("Generate 4 variations for page", selectedPage?.pageNumber);
  }, [selectedPage]);

  const handleGuidesToggle = React.useCallback(() => {
    setGuidesVisible((prev) => !prev);
  }, []);

  // ── Keyboard navigation ─────────────────────────────────────────────────
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when focus is in an input/textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.isContentEditable
      ) {
        return;
      }

      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          setSelectedPageIndex((prev) => Math.max(0, prev - 1));
          break;
        case "ArrowRight":
          e.preventDefault();
          setSelectedPageIndex((prev) =>
            Math.min(pages.length - 1, prev + 1)
          );
          break;
        case "+":
        case "=":
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setZoom((prev) => {
              const levels: ZoomLevel[] = [50, 75, 100, 125, 150];
              const idx = levels.indexOf(prev);
              return idx < levels.length - 1 ? levels[idx + 1] : prev;
            });
          }
          break;
        case "-":
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setZoom((prev) => {
              const levels: ZoomLevel[] = [50, 75, 100, 125, 150];
              const idx = levels.indexOf(prev);
              return idx > 0 ? levels[idx - 1] : prev;
            });
          }
          break;
        case "g":
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setGuidesVisible((prev) => !prev);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [pages.length]);

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div
      className={cn(
        "grid h-full w-full overflow-hidden",
        "[grid-template-columns:200px_1fr_320px]",
        className
      )}
      role="region"
      aria-label="Page Spread Editor"
    >
      {/* Left panel: Page thumbnails */}
      <PageThumbnailStrip
        pages={pages}
        selectedIndex={selectedPageIndex}
        onSelectPage={setSelectedPageIndex}
        onReorderPages={handleReorderPages}
        onAddPage={handleAddPage}
        onDeletePage={handleDeletePage}
      />

      {/* Center panel: Two-page spread view */}
      <SpreadView
        leftPage={leftPageWithLayout}
        rightPage={rightPageWithLayout}
        zoom={zoom}
        onZoomChange={setZoom}
        guidesVisible={guidesVisible}
        onGuidesToggle={handleGuidesToggle}
      />

      {/* Right panel: Properties */}
      <PageProperties
        layout={currentLayout}
        onLayoutChange={handleLayoutChange}
        ageRange={ageRange}
        textProps={currentTextProps}
        onTextPropsChange={handleTextPropsChange}
        illustrationProps={currentIllustrationProps}
        onIllustrationPropsChange={handleIllustrationPropsChange}
        readability={currentReadability}
        onGenerateIllustration={handleGenerateIllustration}
        onUploadImage={handleUploadImage}
        onRegenerate={handleRegenerate}
        onGenerateVariations={handleGenerateVariations}
      />
    </div>
  );
}

export type { SpreadEditorProps };
