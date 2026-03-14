"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Zap,
  Clock,
  Globe,
  FileText,
  Layers,
  Plus,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useComics, useComicStats } from "@/modules/specialty/comic/hooks";
import { ComicCard } from "@/modules/specialty/comic/components/ComicCard";
import { Breadcrumb } from "@/components/ui/breadcrumb";

// ---------------------------------------------------------------------------
// Quick-start templates
// ---------------------------------------------------------------------------

interface QuickTemplate {
  slug: string;
  label: string;
  description: string;
  format: string;
  art_style: string;
  color_mode: string;
}

const QUICK_TEMPLATES: QuickTemplate[] = [
  {
    slug: "superhero-origin",
    label: "Superhero Origin Story",
    description: "Classic superhero tale in full-color American style",
    format: "graphic_novel",
    art_style: "american_classic",
    color_mode: "full_color",
  },
  {
    slug: "manga-adventure",
    label: "Manga Adventure",
    description: "Action-packed manga in traditional black and white",
    format: "manga",
    art_style: "manga",
    color_mode: "black_and_white",
  },
  {
    slug: "indie-slice-of-life",
    label: "Indie Slice-of-Life",
    description: "Intimate indie story with a limited color palette",
    format: "single_issue",
    art_style: "indie",
    color_mode: "limited_palette",
  },
  {
    slug: "noir-detective",
    label: "Noir Detective",
    description: "Moody detective story in grayscale noir style",
    format: "graphic_novel",
    art_style: "noir",
    color_mode: "grayscale",
  },
  {
    slug: "kids-comic",
    label: "Kids Comic",
    description: "Fun, colorful comic for younger readers",
    format: "single_issue",
    art_style: "cartoon",
    color_mode: "full_color",
  },
  {
    slug: "scifi-webcomic",
    label: "Sci-Fi Webcomic",
    description: "Episodic sci-fi series with realistic artwork",
    format: "webcomic",
    art_style: "realistic",
    color_mode: "full_color",
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ComicBooksPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [formatFilter, setFormatFilter] = useState<string>("all");

  const filters = {
    ...(search && { search }),
    ...(statusFilter !== "all" && { status: statusFilter }),
    ...(formatFilter !== "all" && { format: formatFilter }),
  };

  const { data: stats } = useComicStats();
  const { data: comicsData, isLoading } = useComics(1, 50, filters);

  const comics = comicsData?.items ?? [];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <Breadcrumb items={[
        { label: "Specialty", href: "/specialty" },
        { label: "Comic Books" },
      ]} />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Zap className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Comic Books</h1>
            <p className="text-muted-foreground">
              Create comics, graphic novels, and manga with AI-powered tools
            </p>
          </div>
        </div>
        <Button asChild>
          <Link href="/specialty/comic-books/new">
            <Plus className="h-4 w-4 mr-2" /> Create New Comic
          </Link>
        </Button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center">
              <Zap className="h-5 w-5 text-[#3B82F6]" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.total_comics ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Total Comics</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-[#F59E0B]/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-[#F59E0B]" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.in_progress ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">In Progress</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-[#10B981]/10 flex items-center justify-center">
              <Globe className="h-5 w-5 text-[#10B981]" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.published ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Published</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-[#6366F1]/10 flex items-center justify-center">
              <FileText className="h-5 w-5 text-[#6366F1]" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.pages_created ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Pages Created</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search comics..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        <Select value={formatFilter} onValueChange={setFormatFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Format" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Formats</SelectItem>
            <SelectItem value="single_issue">Single Issue</SelectItem>
            <SelectItem value="graphic_novel">Graphic Novel</SelectItem>
            <SelectItem value="manga">Manga</SelectItem>
            <SelectItem value="webcomic">Webcomic</SelectItem>
            <SelectItem value="mini_series">Mini Series</SelectItem>
            <SelectItem value="one_shot">One-Shot</SelectItem>
            <SelectItem value="trade_paperback">Trade Paperback</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Comic Grid or Empty State */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="overflow-hidden animate-pulse">
              <div className="aspect-[3/4] bg-muted" />
              <div className="p-3 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : comics.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {comics.map((comic) => (
            <ComicCard key={comic.id} comic={comic} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <Zap className="h-12 w-12 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No comic books yet</h3>
          <p className="text-muted-foreground max-w-md mb-6">
            Create your first comic book. Choose from graphic novels, manga,
            webcomics, and more — or start from a quick template below.
          </p>
          <Button asChild className="mb-10">
            <Link href="/specialty/comic-books/new">
              <Plus className="h-4 w-4 mr-2" /> Create Your First Comic
            </Link>
          </Button>

          {/* Quick Start Templates */}
          <div className="w-full max-w-4xl">
            <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Layers className="h-5 w-5 text-muted-foreground" />
              Quick Start Templates
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {QUICK_TEMPLATES.map((tpl) => (
                <Link
                  key={tpl.slug}
                  href={"/specialty/comic-books/new?template=" + tpl.slug}
                >
                  <Card className="p-4 hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer h-full">
                    <h5 className="font-semibold text-sm mb-1">{tpl.label}</h5>
                    <p className="text-xs text-muted-foreground mb-2">
                      {tpl.description}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">
                        {tpl.format.replace("_", " ")}
                      </span>
                      <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">
                        {tpl.art_style.replace("_", " ")}
                      </span>
                      <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">
                        {tpl.color_mode.replace("_", " ")}
                      </span>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
