"use client";

import { useMemo } from "react";
import { differenceInDays, format, isWithinInterval, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
import type { LaunchPhase } from "../types";

interface LaunchPhaseTimelineProps {
  phases: LaunchPhase[];
}

const phaseConfig: Record<string, { label: string; bg: string; border: string; text: string }> = {
  pre_launch: {
    label: "Pre-Launch",
    bg: "bg-blue-500",
    border: "border-blue-500",
    text: "text-blue-700",
  },
  launch_week: {
    label: "Launch Week",
    bg: "bg-green-500",
    border: "border-green-500",
    text: "text-green-700",
  },
  post_launch: {
    label: "Post-Launch",
    bg: "bg-purple-500",
    border: "border-purple-500",
    text: "text-purple-700",
  },
};

export function LaunchPhaseTimeline({ phases }: LaunchPhaseTimelineProps) {
  const sortedPhases = useMemo(
    () => [...phases].sort((a, b) => a.order_index - b.order_index),
    [phases]
  );

  const { totalDays, phaseWidths, currentDayPercent } = useMemo(() => {
    if (sortedPhases.length === 0) {
      return { totalDays: 0, phaseWidths: [], currentDayPercent: -1 };
    }

    const startDates = sortedPhases.map((p) => (p.start_date ? parseISO(p.start_date) : new Date()));
    const endDates = sortedPhases.map((p) => (p.end_date ? parseISO(p.end_date) : new Date()));

    const overallStart = startDates.reduce((min, d) => (d < min ? d : min), startDates[0]);
    const overallEnd = endDates.reduce((max, d) => (d > max ? d : max), endDates[0]);

    const total = Math.max(differenceInDays(overallEnd, overallStart), 1);

    const widths = sortedPhases.map((phase) => {
      const start = phase.start_date ? parseISO(phase.start_date) : overallStart;
      const end = phase.end_date ? parseISO(phase.end_date) : overallEnd;
      const days = Math.max(differenceInDays(end, start), 1);
      return Math.max((days / total) * 100, 10); // at least 10% width for visibility
    });

    // Normalize widths to 100%
    const widthSum = widths.reduce((s, w) => s + w, 0);
    const normalizedWidths = widths.map((w) => (w / widthSum) * 100);

    const now = new Date();
    let dayPercent = -1;
    if (now >= overallStart && now <= overallEnd) {
      dayPercent = (differenceInDays(now, overallStart) / total) * 100;
    }

    return { totalDays: total, phaseWidths: normalizedWidths, currentDayPercent: dayPercent };
  }, [sortedPhases]);

  if (sortedPhases.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground text-sm">
        No phases defined for this plan.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Phase bar */}
      <div className="relative flex h-10 rounded-lg overflow-hidden border">
        {sortedPhases.map((phase, idx) => {
          const config = phaseConfig[phase.phase_type] || phaseConfig.pre_launch;
          return (
            <div
              key={phase.id}
              className={cn(
                "flex items-center justify-center text-white text-xs font-medium transition-all",
                config.bg,
                idx > 0 && "border-l-2 border-white/30"
              )}
              style={{ width: `${phaseWidths[idx]}%` }}
              title={`${config.label}: ${phase.start_date ? format(parseISO(phase.start_date), "MMM d") : "?"} - ${phase.end_date ? format(parseISO(phase.end_date), "MMM d") : "?"}`}
            >
              {config.label}
            </div>
          );
        })}

        {/* Current date marker */}
        {currentDayPercent >= 0 && currentDayPercent <= 100 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-red-600 z-10"
            style={{ left: `${currentDayPercent}%` }}
            title={`Today: ${format(new Date(), "MMM d, yyyy")}`}
          >
            <div className="absolute -top-1 -left-1 w-2.5 h-2.5 bg-red-600 rounded-full" />
          </div>
        )}
      </div>

      {/* Date labels */}
      <div className="flex">
        {sortedPhases.map((phase, idx) => {
          const config = phaseConfig[phase.phase_type] || phaseConfig.pre_launch;
          return (
            <div
              key={phase.id}
              className="text-center"
              style={{ width: `${phaseWidths[idx]}%` }}
            >
              <span className={cn("text-xs", config.text)}>
                {phase.start_date ? format(parseISO(phase.start_date), "MMM d") : "?"} -{" "}
                {phase.end_date ? format(parseISO(phase.end_date), "MMM d, yyyy") : "?"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
