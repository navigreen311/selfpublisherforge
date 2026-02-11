"use client";

import { useState } from "react";
import { useGreenlightMutation, type GreenlightResult } from "../hooks";

export function GreenlightScorer() {
  const [formData, setFormData] = useState({
    title: "",
    genre: "",
    sub_genre: "",
    estimated_word_count: 50000,
    estimated_price: 4.99,
    royalty_rate: 0.7,
    estimated_production_cost: 500,
    estimated_marketing_budget: 200,
    is_series: false,
    series_position: 1,
    comparable_asins: "",
    market_size_estimate: 0,
  });

  const mutation = useGreenlightMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const request = {
      title: formData.title,
      genre: formData.genre,
      sub_genre: formData.sub_genre || undefined,
      estimated_word_count: formData.estimated_word_count,
      estimated_price: formData.estimated_price,
      royalty_rate: formData.royalty_rate,
      estimated_production_cost: formData.estimated_production_cost,
      estimated_marketing_budget: formData.estimated_marketing_budget,
      is_series: formData.is_series,
      series_position: formData.is_series ? formData.series_position : undefined,
      comparable_asins: formData.comparable_asins
        ? formData.comparable_asins.split(",").map((a) => a.trim())
        : [],
      market_size_estimate: formData.market_size_estimate || undefined,
    };

    mutation.mutate(request);
  };

  const handleChange = (field: string, value: string | number | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Greenlight Gate</h3>
        <p className="text-sm text-gray-500 mb-6">
          Evaluate a book idea&apos;s ROI potential before writing
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Working Title *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => handleChange("title", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter book title"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Primary Genre *
              </label>
              <input
                type="text"
                required
                value={formData.genre}
                onChange={(e) => handleChange("genre", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Romance, Thriller, Fantasy"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sub-Genre
              </label>
              <input
                type="text"
                value={formData.sub_genre}
                onChange={(e) => handleChange("sub_genre", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Contemporary, Psychological"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Word Count
              </label>
              <input
                type="number"
                value={formData.estimated_word_count}
                onChange={(e) => handleChange("estimated_word_count", parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="5000"
                max="500000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Planned Price ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.estimated_price}
                onChange={(e) => handleChange("estimated_price", parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0.99"
                max="99.99"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Royalty Rate
              </label>
              <select
                value={formData.royalty_rate}
                onChange={(e) => handleChange("royalty_rate", parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="0.35">35% (KDP Select / Wide)</option>
                <option value="0.7">70% (KDP $2.99-$9.99)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Production Cost ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.estimated_production_cost}
                onChange={(e) => handleChange("estimated_production_cost", parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
              />
              <p className="text-xs text-gray-500 mt-1">Cover, editing, formatting</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Marketing Budget ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.estimated_marketing_budget}
                onChange={(e) => handleChange("estimated_marketing_budget", parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
              />
              <p className="text-xs text-gray-500 mt-1">Launch ads and promotion</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_series}
                onChange={(e) => handleChange("is_series", e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">Part of a series</span>
            </label>
            {formData.is_series && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Series Position
                </label>
                <input
                  type="number"
                  value={formData.series_position}
                  onChange={(e) => handleChange("series_position", parseInt(e.target.value))}
                  className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                />
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Comparable ASINs (comma-separated)
            </label>
            <input
              type="text"
              value={formData.comparable_asins}
              onChange={(e) => handleChange("comparable_asins", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="B08XYZ123, B07ABC456"
            />
          </div>

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {mutation.isPending ? "Calculating..." : "Calculate Greenlight Score"}
          </button>
        </form>

        {mutation.isError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800 text-sm">
              Failed to calculate greenlight score. Please try again.
            </p>
          </div>
        )}
      </div>

      {/* Results */}
      {mutation.isSuccess && mutation.data && (
        <GreenlightResult result={mutation.data} />
      )}
    </div>
  );
}

function GreenlightResult({ result }: { result: GreenlightResult }) {
  const recommendationColor =
    result.recommendation === "go"
      ? "bg-green-100 text-green-800 border-green-200"
      : result.recommendation === "caution"
      ? "bg-yellow-100 text-yellow-800 border-yellow-200"
      : "bg-red-100 text-red-800 border-red-200";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{result.title}</h3>
          <p className="text-sm text-gray-500">{result.genre}</p>
        </div>
        <div className={`px-4 py-2 rounded-lg border-2 ${recommendationColor}`}>
          <p className="text-xs font-semibold uppercase">{result.recommendation}</p>
          <p className="text-2xl font-bold">{result.greenlight_score.toFixed(0)}/100</p>
        </div>
      </div>

      {/* Financial Projections */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">First Year ROI</p>
          <p className="text-2xl font-bold text-gray-900">{result.first_year_roi.toFixed(0)}%</p>
          <p className="text-xs text-gray-600 mt-1">
            Profit: ${result.first_year_profit.toLocaleString()}
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Breakeven</p>
          <p className="text-2xl font-bold text-gray-900">
            {result.breakeven_months ? `${result.breakeven_months.toFixed(1)} mo` : "N/A"}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Investment: ${result.total_investment.toLocaleString()}
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Monthly Revenue</p>
          <p className="text-2xl font-bold text-gray-900">
            ${result.projected_monthly_royalty.toLocaleString()}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            {result.projected_monthly_units} units/month
          </p>
        </div>
      </div>

      {/* Risk & Opportunity Factors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {result.risk_factors.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Risk Factors</h4>
            <ul className="space-y-1">
              {result.risk_factors.map((risk, idx) => (
                <li key={idx} className="flex items-start text-sm text-gray-700">
                  <span className="text-red-500 mr-2">⚠</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.opportunity_factors.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Opportunities</h4>
            <ul className="space-y-1">
              {result.opportunity_factors.map((opp, idx) => (
                <li key={idx} className="flex items-start text-sm text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>{opp}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Suggestions to Improve ROI</h4>
          <ul className="space-y-1">
            {result.suggestions.map((suggestion, idx) => (
              <li key={idx} className="flex items-start text-sm text-gray-700">
                <span className="text-blue-500 mr-2">→</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
