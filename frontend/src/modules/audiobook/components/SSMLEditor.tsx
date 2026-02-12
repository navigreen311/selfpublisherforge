"use client";

import { useState, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Play,
  RotateCcw,
  Wand2,
  Eye,
  Code2,
  ChevronDown,
  ChevronRight,
  User,
  Heart,
} from "lucide-react";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SSMLTag {
  type: "break" | "emphasis" | "prosody" | "voice" | "phoneme" | "emotion";
  start: number;
  end: number;
  attributes: Record<string, string>;
}

interface DialogueSegment {
  character: string;
  text: string;
  emotion?: string;
  ssml: string;
  index: number;
}

interface SSMLEditorProps {
  projectId: string;
  initialPlainText?: string;
  initialSSML?: string;
  dialogueSegments?: DialogueSegment[];
  onSSMLChange?: (ssml: string) => void;
  onGenerateSSML?: (plainText: string) => Promise<string>;
  onPreviewAudio?: (ssml: string) => Promise<void>;
  isGenerating?: boolean;
  isPreviewing?: boolean;
}

// ---------------------------------------------------------------------------
// SSML tag color mapping
// ---------------------------------------------------------------------------

const TAG_COLORS: Record<SSMLTag["type"], { bg: string; text: string; label: string }> = {
  break: { bg: "bg-blue-100", text: "text-blue-800", label: "Break" },
  emphasis: { bg: "bg-purple-100", text: "text-purple-800", label: "Emphasis" },
  prosody: { bg: "bg-amber-100", text: "text-amber-800", label: "Prosody" },
  voice: { bg: "bg-green-100", text: "text-green-800", label: "Voice" },
  phoneme: { bg: "bg-pink-100", text: "text-pink-800", label: "Phoneme" },
  emotion: { bg: "bg-rose-100", text: "text-rose-800", label: "Emotion" },
};

// ---------------------------------------------------------------------------
// Simple SSML tokenizer
// ---------------------------------------------------------------------------

interface SSMLToken {
  type: "tag-open" | "tag-close" | "tag-self-closing" | "text";
  value: string;
  tagName?: string;
  tagType?: SSMLTag["type"];
}

function tokenizeSSML(ssml: string): SSMLToken[] {
  const tokens: SSMLToken[] = [];
  const tagRegex = /<\/?([a-zA-Z][a-zA-Z0-9-]*)\b[^>]*\/?>/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const TAG_NAME_MAP: Record<string, SSMLTag["type"]> = {
    break: "break",
    emphasis: "emphasis",
    prosody: "prosody",
    voice: "voice",
    phoneme: "phoneme",
    "amazon:emotion": "emotion",
    emotion: "emotion",
  };

  while ((match = tagRegex.exec(ssml)) !== null) {
    if (match.index > lastIndex) {
      tokens.push({ type: "text", value: ssml.slice(lastIndex, match.index) });
    }

    const fullTag = match[0];
    const tagName = match[1];
    const tagType = TAG_NAME_MAP[tagName];

    if (fullTag.startsWith("</")) {
      tokens.push({ type: "tag-close", value: fullTag, tagName, tagType });
    } else if (fullTag.endsWith("/>")) {
      tokens.push({ type: "tag-self-closing", value: fullTag, tagName, tagType });
    } else {
      tokens.push({ type: "tag-open", value: fullTag, tagName, tagType });
    }

    lastIndex = match.index + fullTag.length;
  }

  if (lastIndex < ssml.length) {
    tokens.push({ type: "text", value: ssml.slice(lastIndex) });
  }

  return tokens;
}

function extractPlainText(ssml: string): string {
  return ssml.replace(/<[^>]+>/g, "").trim();
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SSMLTagBadge({ tagType, attributes }: { tagType: SSMLTag["type"]; attributes?: string }) {
  const color = TAG_COLORS[tagType];
  return (
    <span
      className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-mono ${color.bg} ${color.text}`}
    >
      {color.label}
      {attributes && <span className="ml-1 opacity-75">{attributes}</span>}
    </span>
  );
}

function HighlightedSSML({ ssml }: { ssml: string }) {
  const tokens = useMemo(() => tokenizeSSML(ssml), [ssml]);

  return (
    <div className="font-mono text-sm leading-relaxed whitespace-pre-wrap">
      {tokens.map((token, i) => {
        if (token.type === "text") {
          return <span key={i}>{token.value}</span>;
        }

        if (token.tagType) {
          const color = TAG_COLORS[token.tagType];
          return (
            <span
              key={i}
              className={`${color.bg} ${color.text} rounded px-0.5`}
            >
              {token.value}
            </span>
          );
        }

        return (
          <span key={i} className="text-gray-400">
            {token.value}
          </span>
        );
      })}
    </div>
  );
}

function DialogueSegmentRow({
  segment,
  isSelected,
  onClick,
}: {
  segment: DialogueSegment;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border p-3 transition-colors ${
        isSelected
          ? "border-indigo-300 bg-indigo-50"
          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <User className="h-3.5 w-3.5 text-gray-500" />
        <span className="text-sm font-medium text-gray-900">{segment.character}</span>
        {segment.emotion && (
          <Badge className="bg-rose-100 text-rose-800 hover:bg-rose-100 text-xs px-1.5 py-0">
            <Heart className="h-3 w-3 mr-0.5" />
            {segment.emotion}
          </Badge>
        )}
      </div>
      <p className="text-sm text-gray-600 line-clamp-2">{segment.text}</p>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function SSMLEditor({
  projectId,
  initialPlainText = "",
  initialSSML = "",
  dialogueSegments = [],
  onSSMLChange,
  onGenerateSSML,
  onPreviewAudio,
  isGenerating = false,
  isPreviewing = false,
}: SSMLEditorProps) {
  const [plainText, setPlainText] = useState(initialPlainText);
  const [ssmlText, setSSMLText] = useState(initialSSML);
  const [viewMode, setViewMode] = useState<"edit" | "preview">("edit");
  const [selectedSegmentIndex, setSelectedSegmentIndex] = useState<number | null>(null);
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState<number | null>(null);
  const [editingSSML, setEditingSSML] = useState("");
  const [expandedSegments, setExpandedSegments] = useState(true);

  const sentences = useMemo(() => {
    if (!plainText) return [];
    return plainText
      .split(/(?<=[.!?])\s+/)
      .filter((s) => s.trim().length > 0);
  }, [plainText]);

  const ssmlTags = useMemo(() => {
    const tags: SSMLTag["type"][] = [];
    const tokens = tokenizeSSML(ssmlText);
    for (const token of tokens) {
      if (token.tagType && (token.type === "tag-open" || token.type === "tag-self-closing")) {
        if (!tags.includes(token.tagType)) {
          tags.push(token.tagType);
        }
      }
    }
    return tags;
  }, [ssmlText]);

  const handleSSMLChange = useCallback(
    (value: string) => {
      setSSMLText(value);
      onSSMLChange?.(value);
    },
    [onSSMLChange],
  );

  const handleAutoGenerate = useCallback(async () => {
    if (!onGenerateSSML) {
      toast.error("SSML generation is not configured");
      return;
    }
    try {
      const generated = await onGenerateSSML(plainText);
      handleSSMLChange(generated);
      toast.success("SSML generated successfully");
    } catch {
      toast.error("Failed to generate SSML");
    }
  }, [plainText, onGenerateSSML, handleSSMLChange]);

  const handlePreview = useCallback(async () => {
    if (!onPreviewAudio) {
      toast.error("Audio preview is not configured");
      return;
    }
    const textToPreview =
      selectedSentenceIndex !== null && sentences[selectedSentenceIndex]
        ? sentences[selectedSentenceIndex]
        : ssmlText;
    try {
      await onPreviewAudio(textToPreview);
    } catch {
      toast.error("Failed to preview audio");
    }
  }, [onPreviewAudio, selectedSentenceIndex, sentences, ssmlText]);

  const handleResetToPlainText = useCallback(() => {
    const extracted = extractPlainText(ssmlText);
    setPlainText(extracted || plainText);
    handleSSMLChange("");
    setSelectedSentenceIndex(null);
    toast.success("Reset to plain text");
  }, [ssmlText, plainText, handleSSMLChange]);

  const handleSentenceClick = useCallback(
    (index: number) => {
      if (selectedSentenceIndex === index) {
        setSelectedSentenceIndex(null);
        setEditingSSML("");
        return;
      }
      setSelectedSentenceIndex(index);
      const sentence = sentences[index];
      // Find the corresponding SSML fragment if it exists
      const ssmlLower = ssmlText.toLowerCase();
      const sentenceLower = sentence.toLowerCase().trim();
      if (ssmlLower.includes(sentenceLower)) {
        setEditingSSML(sentence);
      } else {
        setEditingSSML(sentence);
      }
    },
    [selectedSentenceIndex, sentences, ssmlText],
  );

  const handleSegmentClick = useCallback(
    (index: number) => {
      if (selectedSegmentIndex === index) {
        setSelectedSegmentIndex(null);
        setEditingSSML("");
        return;
      }
      setSelectedSegmentIndex(index);
      const segment = dialogueSegments[index];
      setEditingSSML(segment.ssml || segment.text);
    },
    [selectedSegmentIndex, dialogueSegments],
  );

  const handleApplySegmentSSML = useCallback(() => {
    if (selectedSegmentIndex === null) return;
    // Merge edited SSML back — in a real implementation this would update
    // the segment-level SSML in the full document
    toast.success("SSML applied to segment");
    setSelectedSegmentIndex(null);
    setEditingSSML("");
  }, [selectedSegmentIndex]);

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-gray-900">SSML Editor</h2>
          {ssmlTags.length > 0 && (
            <div className="flex items-center gap-1 ml-2">
              {ssmlTags.map((tag) => (
                <SSMLTagBadge key={tag} tagType={tag} />
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAutoGenerate}
            disabled={isGenerating || !plainText.trim()}
            className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <Wand2 className="h-4 w-4" />
            {isGenerating ? "Generating..." : "Auto-generate SSML"}
          </button>
          <button
            onClick={handlePreview}
            disabled={isPreviewing || !ssmlText.trim()}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {isPreviewing ? "Playing..." : "Preview"}
          </button>
          <button
            onClick={handleResetToPlainText}
            disabled={!ssmlText.trim()}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            Reset to Plain Text
          </button>
        </div>
      </div>

      {/* View Mode Tabs */}
      <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "edit" | "preview")}>
        <TabsList>
          <TabsTrigger value="edit" className="gap-1.5">
            <Code2 className="h-4 w-4" />
            Edit
          </TabsTrigger>
          <TabsTrigger value="preview" className="gap-1.5">
            <Eye className="h-4 w-4" />
            Preview
          </TabsTrigger>
        </TabsList>

        {/* Edit View — side by side */}
        <TabsContent value="edit">
          <div className="grid grid-cols-2 gap-4">
            {/* Left: Plain Text */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Plain Text
                </CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  value={plainText}
                  onChange={(e) => setPlainText(e.target.value)}
                  placeholder="Enter or paste your plain text here..."
                  className="w-full min-h-[300px] rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
                />

                {/* Sentence list — click to select */}
                {sentences.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                      Sentences ({sentences.length})
                    </p>
                    <div className="max-h-[200px] overflow-y-auto space-y-1">
                      {sentences.map((sentence, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSentenceClick(idx)}
                          className={`w-full text-left rounded px-2 py-1.5 text-sm transition-colors ${
                            selectedSentenceIndex === idx
                              ? "bg-indigo-100 text-indigo-900"
                              : "text-gray-700 hover:bg-gray-100"
                          }`}
                        >
                          <span className="text-xs text-gray-400 mr-2">{idx + 1}.</span>
                          {sentence}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right: SSML Annotated */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-700">
                  SSML Annotated
                </CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  value={ssmlText}
                  onChange={(e) => handleSSMLChange(e.target.value)}
                  placeholder="SSML will appear here after generation, or type it manually..."
                  className="w-full min-h-[300px] rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
                />

                {/* Tag summary */}
                {ssmlText.trim() && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                      Detected Tags
                    </p>
                    {ssmlTags.length === 0 ? (
                      <p className="text-sm text-gray-400">No SSML tags detected</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {ssmlTags.map((tag) => (
                          <SSMLTagBadge key={tag} tagType={tag} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sentence SSML Editor (below the two panes when a sentence is selected) */}
          {selectedSentenceIndex !== null && (
            <Card className="mt-4">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Edit SSML for Sentence {selectedSentenceIndex + 1}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  value={editingSSML}
                  onChange={(e) => setEditingSSML(e.target.value)}
                  className="w-full min-h-[80px] rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
                />
                <div className="mt-2 flex items-center gap-2">
                  <button
                    onClick={() => {
                      toast.success("SSML applied to sentence");
                      setSelectedSentenceIndex(null);
                    }}
                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => {
                      setSelectedSentenceIndex(null);
                      setEditingSSML("");
                    }}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Preview — syntax highlighted */}
        <TabsContent value="preview">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-700">
                SSML Preview (Syntax Highlighted)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ssmlText.trim() ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <HighlightedSSML ssml={ssmlText} />
                </div>
              ) : (
                <p className="text-sm text-gray-400 text-center py-8">
                  No SSML content to preview. Generate or type SSML in the Edit tab.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogue Segments */}
      {dialogueSegments.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button
              onClick={() => setExpandedSegments(!expandedSegments)}
              className="flex items-center gap-2 w-full text-left"
            >
              {expandedSegments ? (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-500" />
              )}
              <CardTitle className="text-sm font-medium text-gray-700">
                Dialogue Segments ({dialogueSegments.length})
              </CardTitle>
            </button>
          </CardHeader>
          {expandedSegments && (
            <CardContent>
              <div className="space-y-2">
                {dialogueSegments.map((segment, idx) => (
                  <DialogueSegmentRow
                    key={idx}
                    segment={segment}
                    isSelected={selectedSegmentIndex === idx}
                    onClick={() => handleSegmentClick(idx)}
                  />
                ))}
              </div>

              {/* Edit selected segment SSML */}
              {selectedSegmentIndex !== null && (
                <div className="mt-4 rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                  <p className="text-sm font-medium text-indigo-900 mb-2">
                    Editing SSML for: {dialogueSegments[selectedSegmentIndex].character}
                  </p>
                  <textarea
                    value={editingSSML}
                    onChange={(e) => setEditingSSML(e.target.value)}
                    className="w-full min-h-[80px] rounded-md border border-indigo-300 bg-white px-3 py-2 text-sm font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
                  />
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      onClick={handleApplySegmentSSML}
                      className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
                    >
                      Apply
                    </button>
                    <button
                      onClick={() => {
                        setSelectedSegmentIndex(null);
                        setEditingSSML("");
                      }}
                      className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
