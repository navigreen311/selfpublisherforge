"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import Link from "next/link";
import { toast } from "sonner";
import { useCreateProject } from "@/modules/projects/hooks";

const genres = [
  "Fiction",
  "Non-Fiction",
  "Romance",
  "Mystery",
  "Sci-Fi",
  "Fantasy",
  "Self-Help",
  "Business",
  "Biography",
  "Children",
  "Other",
];

export default function NewProjectPage() {
  const router = useRouter();
  const createProject = useCreateProject();
  const [title, setTitle] = React.useState("");
  const [type, setType] = React.useState("");
  const [genre, setGenre] = React.useState("");
  const [penName, setPenName] = React.useState("");
  const [description, setDescription] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !type) return;

    try {
      const result = await createProject.mutateAsync({
        title,
        type: type as "book" | "series" | "course",
        genre: genre || undefined,
        pen_name: penName || undefined,
        description: description || undefined,
      });
      toast.success("Project created successfully");
      router.push(`/projects/${result.id}`);
    } catch {
      toast.error("Failed to create project. Please try again.");
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild aria-label="Back to projects">
          <Link href="/projects">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Create New Project
          </h1>
          <p className="text-muted-foreground">
            Set up a new publishing project
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Project Details</CardTitle>
            <CardDescription>
              Fill in the basic information about your project
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Project Title"
              placeholder="Enter your project title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Project Type</label>
              <Select value={type} onValueChange={setType} required>
                <SelectTrigger>
                  <SelectValue placeholder="Select project type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="book">Book</SelectItem>
                  <SelectItem value="series">Series</SelectItem>
                  <SelectItem value="course">Course</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Genre</label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger>
                  <SelectValue placeholder="Select genre" />
                </SelectTrigger>
                <SelectContent>
                  {genres.map((g) => (
                    <SelectItem key={g} value={g.toLowerCase()}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Input
              label="Pen Name"
              placeholder="Author pen name (optional)"
              value={penName}
              onChange={(e) => setPenName(e.target.value)}
              helperText="Leave blank to use your account name"
            />

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Description</label>
              <Textarea
                placeholder="Brief description of your project..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                autoGrow
                className="min-h-[100px]"
              />
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" type="button" asChild>
              <Link href="/projects">Cancel</Link>
            </Button>
            <Button
              type="submit"
              disabled={!title || !type || createProject.isPending}
            >
              {createProject.isPending ? "Creating..." : "Create Project"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
