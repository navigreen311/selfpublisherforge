"use client";

import React from "react";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

/**
 * ErrorState — spec-compliant shared error state for landing/grid pages.
 *
 * Per Phase 1.1 of the platform spec. Rendered when a fetch fails.
 *
 * Note: there is also a lowercase `error-state.tsx` variant used by older
 * callers; new code should prefer this one.
 */
export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="text-red-300 text-4xl mb-4" aria-hidden>
        ⚠️
      </div>
      <h3 className="text-lg font-medium text-gray-700 mb-2">
        Something went wrong
      </h3>
      <p className="text-sm text-gray-500 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

export default ErrorState;
