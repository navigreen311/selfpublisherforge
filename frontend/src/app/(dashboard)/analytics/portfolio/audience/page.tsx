"use client";

import { useState } from "react";
import { usePortfolioOverview, useAudiencePersonas, useNicheSeasonality } from "@/modules/analytics/hooks";
import { AudienceDNA } from "@/modules/analytics/components/AudienceDNA";
import { SeasonalCalendar } from "@/modules/analytics/components/SeasonalCalendar";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function AudiencePage() {
  const t = useTranslations("analytics");
  const { data: overview } = usePortfolioOverview();
  const [selectedBookId, setSelectedBookId] = useState<string>("");
  const [selectedGenre, setSelectedGenre] = useState<string>("romance");

  // Use the first book from top performers as default
  const defaultBookId = overview?.top_performers[0]?.book_id;
  const bookIdToUse = selectedBookId || defaultBookId || "";

  const {
    data: personas,
    isLoading: personasLoading,
    error: personasError,
  } = useAudiencePersonas(bookIdToUse, selectedGenre);

  const {
    data: seasonality,
    isLoading: seasonalityLoading,
    error: seasonalityError,
  } = useNicheSeasonality(selectedGenre);

  const handleGenreChange = (genre: string) => {
    setSelectedGenre(genre);
  };

  const handleBookChange = (bookId: string) => {
    setSelectedBookId(bookId);
    // Update genre based on selected book
    const book = overview?.top_performers.find((b) => b.book_id === bookId) ||
                 overview?.underperformers.find((b) => b.book_id === bookId);
    if (book) {
      setSelectedGenre(book.genre);
    }
  };

  const allBooks = overview
    ? [...overview.top_performers, ...overview.underperformers]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/analytics/portfolio"
            className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block"
          >
            {t("audience.backToPortfolio")}
          </Link>
          <h1 className="text-2xl font-bold text-foreground">{t("audience.title")}</h1>
        </div>
        <Link
          href="/analytics/portfolio/greenlight"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          {t("audience.greenlightGate")}
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t("audience.selectBook")}
            </label>
            <select
              value={bookIdToUse}
              onChange={(e) => handleBookChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allBooks.length === 0 && (
                <option value="">{t("audience.noBooksAvailable")}</option>
              )}
              {allBooks.map((book) => (
                <option key={book.book_id} value={book.book_id}>
                  {book.title} ({book.genre})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t("audience.genreNiche")}
            </label>
            <input
              type="text"
              value={selectedGenre}
              onChange={(e) => handleGenreChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t("audience.genrePlaceholder")}
            />
          </div>
        </div>
      </div>

      {/* Audience Personas */}
      {personasLoading ? (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <Skeleton className="h-8 w-48 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : personasError ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{t("audience.errorPersonas")}</p>
        </div>
      ) : personas && personas.length > 0 ? (
        <AudienceDNA personas={personas} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{t("audience.noAudienceDataTitle")}</h3>
          <p className="text-gray-600">
            {t("audience.noAudienceDataDescription")}
          </p>
        </div>
      )}

      {/* Seasonal Calendar */}
      {seasonalityLoading ? (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <Skeleton className="h-8 w-48 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : seasonalityError ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <p className="text-yellow-800">
            {t("audience.errorSeasonality")}
          </p>
        </div>
      ) : seasonality ? (
        <SeasonalCalendar seasonality={seasonality} />
      ) : null}
    </div>
  );
}
