"use client";

import Link from "next/link";
import { MoreHorizontal, Pencil, Copy, Trash2, FileText, BookOpen } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ProfileResponse } from "../types";

interface ProfileCardProps {
  profile: ProfileResponse;
  onDelete?: (id: string) => void;
}

export function ProfileCard({ profile, onDelete }: ProfileCardProps) {
  const hasStyleCard = profile.style_card !== null;
  const keyMetrics = profile.style_card?.key_metrics;

  return (
    <Card className="group relative flex flex-col transition-shadow hover:shadow-lg">
      <CardHeader className="pb-3">
        {/* Name + active indicator */}
        <div className="flex items-center gap-2">
          {hasStyleCard && (
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-green-500"
              aria-label="Style card active"
            />
          )}
          <h3 className="font-semibold text-lg leading-tight line-clamp-1">
            {profile.name}
          </h3>
        </div>

        {/* Genre badge */}
        {profile.genre && (
          <div className="mt-1.5">
            <Badge variant="secondary">{profile.genre}</Badge>
          </div>
        )}
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-4 pt-0">
        {/* Voice fingerprint summary */}
        {profile.style_card?.summary && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {profile.style_card.summary}
          </p>
        )}

        {/* Key metrics row */}
        {keyMetrics && (
          <div className="grid grid-cols-3 gap-2 rounded-md bg-muted/50 px-3 py-2 text-center text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Readability</div>
              <div className="font-semibold">
                {keyMetrics.reading_level != null
                  ? keyMetrics.reading_level.toFixed(1)
                  : "—"}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Formality</div>
              <div className="font-semibold">
                {keyMetrics.formality != null
                  ? `${Math.round(keyMetrics.formality * 100)}%`
                  : "—"}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Warmth</div>
              <div className="font-semibold">
                {keyMetrics.warmth != null
                  ? `${Math.round(keyMetrics.warmth * 100)}%`
                  : "—"}
              </div>
            </div>
          </div>
        )}

        {/* Sample count & word count */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
            {profile.sample_count} sample{profile.sample_count !== 1 ? "s" : ""}
          </span>
          <span className="flex items-center gap-1">
            <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
            {profile.word_count.toLocaleString()} words
          </span>
        </div>

        {/* Action buttons */}
        <div className="mt-auto flex items-center gap-2 border-t pt-3">
          <Button variant="outline" size="sm" asChild className="flex-1">
            <Link href={`/style-profiles/${profile.id}`}>View Profile</Link>
          </Button>

          <Button variant="secondary" size="sm" asChild className="flex-1">
            <Link href={`/style-profiles/${profile.id}?tab=test`}>
              Test Style
            </Link>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">More actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link href={`/style-profiles/${profile.id}?edit=true`}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => onDelete?.(profile.id)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardContent>
    </Card>
  );
}
