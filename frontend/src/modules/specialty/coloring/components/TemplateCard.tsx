"use client";

import { type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export interface TemplateCardProps {
  icon: LucideIcon;
  name: string;
  description: string;
  onUseTemplate: () => void;
}

export function TemplateCard({
  icon: Icon,
  name,
  description,
  onUseTemplate,
}: TemplateCardProps) {
  return (
    <Card className="flex flex-col hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2.5">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <CardTitle className="text-base">{name}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <CardDescription className="text-sm">{description}</CardDescription>
      </CardContent>
      <CardFooter className="pt-0">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={onUseTemplate}
        >
          Use Template
        </Button>
      </CardFooter>
    </Card>
  );
}
