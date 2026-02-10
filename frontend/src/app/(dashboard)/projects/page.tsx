"use client";

import * as React from "react";
import Link from "next/link";
import { Plus, Search, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";

interface ProjectItem {
  id: string;
  title: string;
  type: "book" | "series" | "course";
  status: "draft" | "active" | "archived";
  booksCount: number;
  updatedAt: string;
}

const sampleProjects: ProjectItem[] = [
  {
    id: "1",
    title: "The Art of Self-Publishing",
    type: "book",
    status: "active",
    booksCount: 1,
    updatedAt: "2024-12-15",
  },
  {
    id: "2",
    title: "Summer Romance Series",
    type: "series",
    status: "draft",
    booksCount: 3,
    updatedAt: "2024-12-10",
  },
  {
    id: "3",
    title: "Writing Mastery Guide",
    type: "book",
    status: "active",
    booksCount: 1,
    updatedAt: "2024-12-08",
  },
  {
    id: "4",
    title: "Productivity Masterclass",
    type: "course",
    status: "archived",
    booksCount: 5,
    updatedAt: "2024-11-20",
  },
];

const badgeVariant = (status: string) => {
  switch (status) {
    case "active":
      return "default" as const;
    case "draft":
      return "secondary" as const;
    case "archived":
      return "outline" as const;
    default:
      return "secondary" as const;
  }
};

export default function ProjectsPage() {
  const [search, setSearch] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState("all");
  const [statusFilter, setStatusFilter] = React.useState("all");

  const filteredProjects = sampleProjects.filter((p) => {
    const matchesSearch = p.title.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || p.type === typeFilter;
    const matchesStatus = statusFilter === "all" || p.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">
            Manage all your publishing projects
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="book">Book</SelectItem>
            <SelectItem value="series">Series</SelectItem>
            <SelectItem value="course">Course</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No projects found"
          description="Try adjusting your search or filters, or create a new project to get started."
          actionLabel="Create Project"
          onAction={() => (window.location.href = "/projects/new")}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{project.title}</CardTitle>
                    <Badge variant={badgeVariant(project.status)}>
                      {project.status}
                    </Badge>
                  </div>
                  <CardDescription className="capitalize">
                    {project.type}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>
                      {project.booksCount}{" "}
                      {project.booksCount === 1 ? "book" : "books"}
                    </span>
                    <span>
                      Updated{" "}
                      {new Date(project.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
