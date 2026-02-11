"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Image as ImageIcon } from "lucide-react";
import { CoverGenerator } from "@/modules/cover-design/components/CoverGenerator";
import { TemplateSelector } from "@/modules/cover-design/components/TemplateSelector";

type TabType = "generate" | "templates";

export default function NewCoverPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("generate");

  const handleSuccess = (coverId: string) => {
    router.push(`/cover-design/${coverId}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          aria-label="Go back"
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold">Create New Cover</h1>
          <p className="text-sm text-muted-foreground">
            Generate a custom book cover with AI or browse templates
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab("generate")}
            className={`flex items-center gap-2 pb-3 px-1 border-b-2 transition-colors ${
              activeTab === "generate"
                ? "border-primary text-primary font-medium"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="h-4 w-4" />
            AI Generator
          </button>
          <button
            onClick={() => setActiveTab("templates")}
            className={`flex items-center gap-2 pb-3 px-1 border-b-2 transition-colors ${
              activeTab === "templates"
                ? "border-primary text-primary font-medium"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <ImageIcon className="h-4 w-4" />
            Templates
          </button>
        </div>
      </div>

      {/* Tab content */}
      <div className="py-4">
        {activeTab === "generate" && (
          <div className="max-w-3xl">
            <CoverGenerator onSuccess={handleSuccess} />
          </div>
        )}
        {activeTab === "templates" && (
          <div>
            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                Browse and select from our professionally designed templates.
                You can customize them after selection.
              </p>
            </div>
            <TemplateSelector
              onSelectTemplate={(template) => {
                console.log("Selected template:", template);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
