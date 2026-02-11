"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Layers, GraduationCap } from "lucide-react";
import type { Project } from "../types";

const typeIcons = {
  book: BookOpen,
  series: Layers,
  course: GraduationCap,
} as const;

const statusColors = {
  draft: "bg-gray-100 text-gray-800",
  active: "bg-blue-100 text-blue-800",
  archived: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
} as const;

interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  const Icon = typeIcons[project.type] || BookOpen;

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{project.title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <Badge variant="outline" className={statusColors[project.status]}>
            {project.status}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {project.books.length} book{project.books.length !== 1 ? "s" : ""}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
