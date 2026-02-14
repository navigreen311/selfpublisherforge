"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Palette } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CoverGallery } from "@/modules/cover-design/components/CoverGallery";
import { TemplateGallery } from "@/modules/cover-design/components/TemplateGallery";
import { CompetitorCovers } from "@/modules/cover-design/components/CompetitorCovers";
import { useCovers } from "@/modules/cover-design/hooks";

const FORMAT_OPTIONS = [
  { value: "all", label: "All Formats" },
  { value: "amazon-kdp", label: "Amazon KDP" },
  { value: "ingram-spark", label: "IngramSpark" },
  { value: "barnes-noble", label: "Barnes & Noble" },
  { value: "apple-books", label: "Apple Books" },
  { value: "google-play", label: "Google Play" },
  { value: "custom", label: "Custom" },
];

const SORT_OPTIONS = [
  { value: "recent", label: "Recent" },
  { value: "oldest", label: "Oldest" },
  { value: "title-asc", label: "Title A-Z" },
  { value: "title-desc", label: "Title Z-A" },
];

export default function CoverDesignPage() {
  const t = useTranslations("cover-design");
  const router = useRouter();
  const { data: covers, isPending } = useCovers();

  const [selectedTab, setSelectedTab] = useState("my-covers");
  const [selectedProject, setSelectedProject] = useState("all");
  const [selectedFormat, setSelectedFormat] = useState("all");
  const [selectedSort, setSelectedSort] = useState("recent");

  // Filter and sort covers
  const filteredCovers = (covers || [])
    .filter((cover) => {
      if (selectedFormat !== "all" && cover.platform !== selectedFormat) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      switch (selectedSort) {
        case "recent":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case "oldest":
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case "title-asc":
          return a.title.localeCompare(b.title);
        case "title-desc":
          return b.title.localeCompare(a.title);
        default:
          return 0;
      }
    });

  const hasCovers = covers && covers.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Palette className="h-6 w-6 text-primary" aria-hidden="true" />
            <h1 className="text-2xl font-bold">{t("title") || "Cover Design Studio"}</h1>
          </div>
          <p className="text-muted-foreground">
            {t("description") || "Create stunning book covers with AI-powered design."}
          </p>
        </div>
        <Button
          onClick={() => router.push("/cover-design/new")}
          className="gap-2"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t("generateCover") || "Generate Cover"}
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="my-covers">My Covers</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="competitor-covers">Competitor Covers</TabsTrigger>
        </TabsList>

        {/* My Covers Tab */}
        <TabsContent value="my-covers" className="space-y-6">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger className="sm:w-[200px]">
                <SelectValue placeholder="All Projects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedFormat} onValueChange={setSelectedFormat}>
              <SelectTrigger className="sm:w-[200px]">
                <SelectValue placeholder="All Formats" />
              </SelectTrigger>
              <SelectContent>
                {FORMAT_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedSort} onValueChange={setSelectedSort}>
              <SelectTrigger className="sm:w-[200px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Cover Gallery or Empty State */}
          {hasCovers ? (
            <CoverGallery
              covers={filteredCovers}
              isLoading={isPending}
              emptyMessage={
                selectedFormat !== "all" || selectedProject !== "all"
                  ? "No covers match your filters."
                  : t("noCoverMessage") || "No covers yet."
              }
            />
          ) : (
            <div className="text-center py-12 border-2 border-dashed rounded-lg">
              <Palette className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-lg font-semibold mb-2">No covers yet</p>
              <p className="text-muted-foreground mb-6">
                Generate your first AI cover or start from a template.
              </p>
              <div className="flex justify-center gap-4">
                <Button onClick={() => router.push("/cover-design/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  Generate Cover
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedTab("templates")}
                >
                  Browse Templates
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <TemplateGallery
            onSelectTemplate={(template) => {
              // Navigate to new cover page with template pre-selected
              router.push(`/cover-design/new?template=${template.id}`);
            }}
          />
        </TabsContent>

        {/* Competitor Covers Tab */}
        <TabsContent value="competitor-covers" className="space-y-6">
          <CompetitorCovers />
        </TabsContent>
      </Tabs>
    </div>
  );
}
