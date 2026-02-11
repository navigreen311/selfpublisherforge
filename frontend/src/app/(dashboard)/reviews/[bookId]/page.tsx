"use client";

import { ReviewDashboard } from "@/modules/reviews/components/ReviewDashboard";
import Link from "next/link";
import { use } from "react";

interface BookReviewPageProps {
  params: Promise<{
    bookId: string;
  }>;
}

export default function BookReviewPage({ params }: BookReviewPageProps) {
  const resolvedParams = use(params);
  const { bookId } = resolvedParams;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href="/reviews"
          className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
        >
          ← Back to All Reviews
        </Link>
      </div>

      <ReviewDashboard bookId={bookId} bookTitle={`Book ${bookId}`} />
    </div>
  );
}
