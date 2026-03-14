"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Clock,
  Globe,
  FileText,
  Plus,
  Search,
  Sparkles,
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
import { useChildrensBooks, useChildrensBookStats } from "@/modules/specialty/childrens/hooks";
import { BookCard } from "@/modules/specialty/childrens/components/BookCard";

export default function ChildrensBooksPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [ageFilter, setAgeFilter] = useState<string>("all");

  const filters = {
    ...(search && { search }),
    ...(statusFilter !== "all" && { status: statusFilter }),
    ...(ageFilter !== "all" && { age_range: ageFilter }),
  };

  const { data: stats } = useChildrensBookStats();
  const { data: booksData, isLoading, isError } = useChildrensBooks(1, 50, filters);

  const books = booksData?.items ?? [];

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Children&apos;s Books</h1>
            <p className="text-muted-foreground">
              Create illustrated children&apos;s books with AI-generated artwork
            </p>
          </div>
        </div>
        <Button asChild>
          <Link href="/specialty/childrens-books/new">
            <Plus className="h-4 w-4 mr-2" /> Create New Book
          </Link>
        </Button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats?.total_books ?? 0}
              </p>
              <p className="text-xs text-muted-foreground">Total Books</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-500" />
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
            <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <Globe className="h-5 w-5 text-green-500" />
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
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <FileText className="h-5 w-5 text-blue-500" />
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
            placeholder="Search books..."
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
            <SelectItem value="in-progress">In Progress</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        <Select value={ageFilter} onValueChange={setAgeFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Age Range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Ages</SelectItem>
            <SelectItem value="board">Board (0-3)</SelectItem>
            <SelectItem value="picture">Picture (3-5)</SelectItem>
            <SelectItem value="early_reader">Early Reader (5-8)</SelectItem>
            <SelectItem value="chapter">Chapter (8-12)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Book Grid, Error, or Empty State */}
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
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-24 w-24 rounded-full bg-destructive/10 flex items-center justify-center mb-6">
            <BookOpen className="h-12 w-12 text-destructive" />
          </div>
          <h3 className="text-xl font-semibold mb-2">
            Failed to load books
          </h3>
          <p className="text-muted-foreground max-w-md mb-6">
            Something went wrong while fetching your children&apos;s books.
            Please try again later.
          </p>
        </div>
      ) : books.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <BookOpen className="h-12 w-12 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">
            No children&apos;s books yet
          </h3>
          <p className="text-muted-foreground max-w-md mb-6">
            Create your first illustrated children&apos;s book with AI-generated artwork.
          </p>
          <Button asChild>
            <Link href="/specialty/childrens-books/new">
              <Plus className="h-4 w-4 mr-2" /> Create Your First Book
            </Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </div>
  );
}
