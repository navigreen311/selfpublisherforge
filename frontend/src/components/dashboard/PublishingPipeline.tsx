"use client";

import { useTranslations } from "@/hooks/use-translations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface PipelineStage {
  name: string;
  count: number;
  projects: { id: string; title: string }[];
}

interface PublishingPipelineProps {
  stages?: PipelineStage[];
}

const defaultStages: PipelineStage[] = [
  { name: "drafting", count: 0, projects: [] },
  { name: "editing", count: 0, projects: [] },
  { name: "formatting", count: 0, projects: [] },
  { name: "publishing", count: 0, projects: [] },
  { name: "published", count: 0, projects: [] },
];

const stageColors: Record<string, string> = {
  drafting: "bg-blue-500",
  editing: "bg-yellow-500",
  formatting: "bg-orange-500",
  publishing: "bg-purple-500",
  published: "bg-green-500",
};

const stageRingColors: Record<string, string> = {
  drafting: "ring-blue-500",
  editing: "ring-yellow-500",
  formatting: "ring-orange-500",
  publishing: "ring-purple-500",
  published: "ring-green-500",
};

export function PublishingPipeline({ stages }: PublishingPipelineProps) {
  const t = useTranslations("dashboard");
  const pipelineStages = stages ?? defaultStages;

  const hasProjects = pipelineStages.some((stage) => stage.count > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("publishingPipeline.title")}</CardTitle>
        <CardDescription>{t("publishingPipeline.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent>
        {hasProjects ? (
          <>
            <div className="flex flex-col items-stretch gap-4 md:flex-row md:items-start md:gap-0">
              {pipelineStages.map((stage, index) => (
                <div key={stage.name} className="flex flex-col items-center md:flex-row md:flex-1">
                  {/* Stage column */}
                  <div className="flex flex-1 flex-col items-center text-center">
                    <span className="text-sm font-medium">
                      {t(`publishingPipeline.${stage.name}`)}
                    </span>
                    <span className="mt-1 text-2xl font-bold">{stage.count}</span>
                    <div className="mt-2 flex flex-wrap justify-center gap-1">
                      {stage.projects.map((project) => (
                        <Link key={project.id} href={`/projects/${project.id}`}>
                          <span
                            title={project.title}
                            className={`inline-block h-3 w-3 cursor-pointer rounded-full mx-0.5 hover:ring-2 ${stageColors[stage.name] ?? "bg-gray-500"} ${stageRingColors[stage.name] ?? "ring-gray-500"}`}
                          />
                        </Link>
                      ))}
                    </div>
                  </div>

                  {/* Arrow between stages */}
                  {index < pipelineStages.length - 1 && (
                    <>
                      {/* Horizontal arrow for desktop */}
                      <span className="hidden text-muted-foreground mx-1 text-lg md:inline-block">
                        &rarr;
                      </span>
                      {/* Vertical arrow for mobile */}
                      <span className="text-muted-foreground my-1 text-lg md:hidden">
                        &darr;
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-6 text-center">
              <Button variant="outline" asChild>
                <Link href="/projects">{t("publishingPipeline.viewAll")}</Link>
              </Button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <p className="text-muted-foreground">
              {t("publishingPipeline.noProjects")}
            </p>
            <Button variant="outline" asChild>
              <Link href="/projects">{t("publishingPipeline.viewAll")}</Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
