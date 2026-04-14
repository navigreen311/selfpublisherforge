"use client";

import React from "react";

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * EmptyState — spec-compliant shared empty state for landing/grid pages.
 *
 * Per Phase 1.1 of the platform spec. Paired with ErrorState and rendered
 * when a successful fetch returns zero items.
 *
 * Note: there is also a lowercase `empty-state.tsx` variant used by older
 * callers; new code should prefer this one.
 */
export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 px-4
                 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50"
    >
      <div className="text-gray-300 text-5xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-700 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 text-center max-w-md mb-6">
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default EmptyState;
