"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Book,
  Palette,
  Plus,
  Search,
  Loader2,
  PawPrint,
  Flower2,
  Sword,
  TreePine,
  Snowflake,
  Rocket,
  CakeSlice,
  Hexagon,
  FileText,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { TemplateCard } from "@/modules/specialty/coloring/components/TemplateCard";
import { BookCard } from "@/modules/specialty/coloring/components/BookCard";
import { useColoringBooks } from "@/modules/specialty/coloring/hooks";

// ─── Templates ────────────────────────────────────────────────────────────────

const TEMPLATES = [
  {
    id: "animals",
    icon: PawPrint,
    name: "Animals & Wildlife",
    description:
      "Lions, elephants, birds, and sea creatures in detailed line art.",
  },
  {
    id: "mandalas",
    icon: Flower2,
    name: "Mandalas & Patterns",
    description:
      "Intricate circular mandala designs with repeating symmetry.",
  },
  {
    id: "fantasy",
    icon: Sword,
    name: "Fantasy Worlds",
    description:
      "Dragons, castles, fairies, and enchanted forests to color.",
  },
  {
    id: "nature",
    icon: TreePine,
    name: "Nature Scenes",
    description:
      "Landscapes, gardens, flowers, and tranquil outdoor scenes.",
  },
  {
    id: "holidays",
    icon: Snowflake,
    name: "Holidays & Seasons",
    description:
      "Christmas, Halloween, Easter, and seasonal celebrations.",
  },
  {
    id: "space",
    icon: Rocket,
    name: "Space & Sci-Fi",
    description:
      "Planets, rockets, aliens, and futuristic cityscapes.",
  },
  {
    id: "food",
    icon: CakeSlice,
    name: "Food & Desserts",
    description:
      "Cupcakes, fruits, sweets, and delicious dishes to color.",
  },
  {
    id: "geometric",
    icon: Hexagon,
    name: "Geometric Abstract",
    description:
      "Tessellations, op-art illusions, and abstract geometric forms.",
  },
] as const;

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ColoringBooksPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data, isLoading, error } = useColoringBooks({
    search: search || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const books = data?.items ?? [];

  // Compute stats - always resolve to 0 when no data
  const totalBooks = data?.total ?? 0;
  const inProgress = books.filter((b) => b.status === "in_progress").length;
  const published = books.filter((b) => b.status === "published").length;
  const pagesCreated = books.reduce((sum, b) => sum + b.pages_created, 0);

  const handleUseTemplate = (templateId: string) => {
    router.push(`/specialty/coloring-books/new?template=${templateId}`);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Coloring Books</h1>
          <p className="text-muted-foreground mt-1">
            Create beautiful coloring books with AI-generated line art
          </p>
        </div>
        <Button asChild>
          <Link href="/specialty/coloring-books/new">
            <Plus className="h-4 w-4 mr-2" />
            New Coloring Book
          </Link>
        </Button>
      </div>

      {/* Stat Cards - always render values (0 when empty), never skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Book} label="Total Books" value={totalBooks} />
        <StatCard icon={BarChart3} label="In Progress" value={inProgress} />
        <StatCard icon={CheckCircle2} label="Published" value={published} />
        <StatCard icon={FileText} label="Pages Created" value={pagesCreated} />
      </div>

      {/* Quick-Start Templates */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Quick-Start Templates</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {TEMPLATES.map((t) => (
            <TemplateCard
              key={t.id}
              icon={t.icon}
              name={t.name}
              description={t.description}
              onUseTemplate={() => handleUseTemplate(t.id)}
            />
          ))}
        </div>
      </section>

      {/* Book Grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Your Books</h2>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search books..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 w-60"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="published">Published</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {isLoading && !data ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-72 rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
            Failed to load coloring books. Please try again.
          </div>
        ) : books.length === 0 ? (
          <div className="border rounded-lg p-12 text-center">
            <Palette className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
            <h3 className="text-lg font-medium mb-2">No coloring books yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first coloring book or start from a template above.
            </p>
            <Button asChild>
              <Link href="/specialty/coloring-books/new">
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Book
              </Link>
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Book;
  label: string;
  value: number;
}) {
  return (
    <div className="border rounded-lg p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-primary/10 p-2">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}
