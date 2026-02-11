"use client";

import { ReviewDashboard } from "@/modules/reviews/components/ReviewDashboard";
import Link from "next/link";
import { use } from "react";
import { useTranslations } from "@/hooks/use-translations";

interface BookReviewPageProps {
  params: Promise<{
    bookId: string;
  }>;
}

export default function BookReviewPage({ params }: BookReviewPageProps) {
  const resolvedParams = use(params);
  const { bookId } = resolvedParams;
  const t = useTranslations("reviews");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href="/reviews"
          className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
        >
          ← {t("detail.backToAllReviews")}
        </Link>
      </div>

      <ReviewDashboard bookId={bookId} bookTitle={t("detail.bookTitle", { id: bookId })} />
    </div>
  );
}
