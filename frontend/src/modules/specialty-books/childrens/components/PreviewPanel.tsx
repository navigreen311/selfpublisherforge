"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Monitor, Smartphone, BookOpen, Eye } from "lucide-react";
import { useChildrensBookEditorStore } from "../store";
import { useBookPages } from "../hooks";
import type { BookPage, PreviewDevice } from "../types";

export interface PreviewPanelProps {
  bookId: string;
}

function PagePreview({ page }: { page: BookPage }) {
  return (
    <div className="bg-white border rounded-md overflow-hidden aspect-[3/4]">
      {page.illustration.image_url ? (
        <div className="relative w-full h-full">
          <img src={page.illustration.image_url} alt="" className="w-full h-full object-cover" />
          {page.text.content && (
            <div
              className={cn(
                "absolute inset-x-0 p-2 bg-white/80",
                page.text.position === "top" && "top-0",
                page.text.position === "bottom" && "bottom-0",
                page.text.position === "middle" && "top-1/2 -translate-y-1/2",
              )}
            >
              <p
                className="text-center"
                style={{
                  fontFamily: page.text.font,
                  fontSize: `${Math.max(8, page.text.size * 0.4)}px`,
                  color: page.text.color,
                }}
              >
                {page.text.content}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-muted">
          <span className="text-xs text-muted-foreground">{page.page_number}</span>
        </div>
      )}
    </div>
  );
}

function DeviceFrame({
  device,
  children,
}: {
  device: PreviewDevice;
  children: React.ReactNode;
}) {
  if (device === "phone") {
    return (
      <div className="mx-auto w-[280px] bg-black rounded-[2rem] p-3 shadow-xl">
        <div className="bg-white rounded-[1.5rem] overflow-hidden">{children}</div>
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-2xl bg-gray-200 rounded-lg p-2 shadow-xl">
      <div className="bg-gray-300 rounded-t-md px-3 py-1 flex items-center gap-2 mb-1">
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-red-400" />
          <div className="w-2 h-2 rounded-full bg-yellow-400" />
          <div className="w-2 h-2 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 bg-white rounded-sm h-4 mx-2" />
      </div>
      <div className="bg-white rounded-b-md overflow-hidden">{children}</div>
    </div>
  );
}

export function PreviewPanel({ bookId }: PreviewPanelProps) {
  const { data: pages = [] } = useBookPages(bookId);
  const { previewDevice, setPreviewDevice } = useChildrensBookEditorStore();

  const sortedPages = [...pages].sort((a, b) => a.page_number - b.page_number);
  const previewPages = sortedPages.slice(0, Math.ceil(sortedPages.length * 0.1) || 3);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Preview</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant={previewDevice === "desktop" ? "default" : "ghost"}
            className="h-7 w-7"
            onClick={() => setPreviewDevice("desktop")}
          >
            <Monitor className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="icon"
            variant={previewDevice === "phone" ? "default" : "ghost"}
            className="h-7 w-7"
            onClick={() => setPreviewDevice("phone")}
          >
            <Smartphone className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          {/* Spread View */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              Spread View
            </h4>
            <div className="grid grid-cols-2 gap-1">
              {sortedPages.map((page) => (
                <PagePreview key={page.id} page={page} />
              ))}
            </div>
          </div>

          {/* Look Inside Simulator */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              &#34;Look Inside&#34; Preview (first 10%)
            </h4>
            <DeviceFrame device={previewDevice}>
              <div className={cn("space-y-1 p-2", previewDevice === "phone" ? "max-h-[400px]" : "max-h-[500px]")}>
                {previewPages.map((page) => (
                  <PagePreview key={page.id} page={page} />
                ))}
              </div>
            </DeviceFrame>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
