"use client";

import { type PortfolioOverview as PortfolioOverviewType } from "../hooks";

interface PortfolioOverviewProps {
  overview: PortfolioOverviewType;
}

export function PortfolioOverview({ overview }: PortfolioOverviewProps) {
  const trendIcon = overview.monthly_trend > 0 ? "↑" : overview.monthly_trend < 0 ? "↓" : "→";
  const trendColor = overview.monthly_trend > 0 ? "text-green-600" : overview.monthly_trend < 0 ? "text-red-600" : "text-gray-500";

  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Total Books</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{overview.total_books}</p>
          <p className="mt-1 text-xs text-gray-500">{overview.active_books} active</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Portfolio ROI</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {overview.portfolio_roi.toFixed(1)}%
          </p>
          <p className="mt-1 text-xs text-gray-500">
            ${overview.total_revenue.toLocaleString()} / ${overview.total_investment.toLocaleString()}
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
          <div className="flex items-baseline gap-2">
            <p className="mt-2 text-3xl font-bold text-gray-900">
              ${overview.monthly_revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </p>
            <span className={`text-sm font-medium ${trendColor}`}>
              {trendIcon} {Math.abs(overview.monthly_trend).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-500">Last 30 days</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Total Revenue</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            ${overview.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </p>
          <p className="mt-1 text-xs text-gray-500">All-time</p>
        </div>
      </div>

      {/* Top/Bottom Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performers */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performers</h3>
          {overview.top_performers.length > 0 ? (
            <div className="space-y-3">
              {overview.top_performers.slice(0, 5).map((book) => (
                <div key={book.book_id} className="flex justify-between items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{book.title}</p>
                    <p className="text-xs text-gray-500">{book.genre}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-green-600">{book.roi.toFixed(0)}% ROI</p>
                    <p className="text-xs text-gray-500">${book.total_revenue.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No top performers yet</p>
          )}
        </div>

        {/* Underperformers */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Needs Attention</h3>
          {overview.underperformers.length > 0 ? (
            <div className="space-y-3">
              {overview.underperformers.slice(0, 5).map((book) => (
                <div key={book.book_id} className="flex justify-between items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{book.title}</p>
                    <p className="text-xs text-gray-500">{book.genre}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-red-600">{book.roi.toFixed(0)}% ROI</p>
                    <p className="text-xs text-gray-500">${book.total_revenue.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No underperformers</p>
          )}
        </div>
      </div>

      {/* Genre Distribution */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Genre</h3>
        {Object.keys(overview.revenue_by_genre).length > 0 ? (
          <div className="space-y-3">
            {Object.entries(overview.revenue_by_genre)
              .sort(([, a], [, b]) => b - a)
              .map(([genre, revenue]) => {
                const count = overview.genre_distribution[genre] || 0;
                const percentage = overview.total_revenue > 0 ? (revenue / overview.total_revenue) * 100 : 0;
                return (
                  <div key={genre}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-900 capitalize">{genre}</span>
                      <span className="text-gray-600">
                        ${revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}{" "}
                        ({count} {count === 1 ? "book" : "books"})
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No genre data available</p>
        )}
      </div>
    </div>
  );
}
