"use client";

import { GreenlightScorer } from "@/modules/analytics/components/GreenlightScorer";
import Link from "next/link";

export default function GreenlightPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/analytics/portfolio"
            className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block"
          >
            ← Back to Portfolio
          </Link>
          <h1 className="text-2xl font-bold text-foreground">Greenlight Gate</h1>
          <p className="text-sm text-gray-600 mt-1">
            Evaluate book ideas before writing to maximize ROI
          </p>
        </div>
        <Link
          href="/analytics/portfolio/audience"
          className="px-4 py-2 text-sm font-medium text-foreground bg-card border rounded-md hover:bg-muted"
        >
          Audience DNA
        </Link>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Pre-Writing ROI Forecast</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                The Greenlight Gate helps you evaluate book ideas before investing time and money.
                Enter your concept details to get:
              </p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>ROI forecast and breakeven analysis</li>
                <li>Market size and capture rate estimates</li>
                <li>Risk factors and opportunity identification</li>
                <li>Go / Caution / No-Go recommendation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Greenlight Scorer Component */}
      <GreenlightScorer />

      {/* Tips Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-3">Tips for Better Results</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>
              <strong>Be realistic with costs:</strong> Include cover design, editing, formatting,
              and initial marketing spend.
            </p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>
              <strong>Research comparable titles:</strong> Find ASINs of similar books in your
              niche for better market size estimates.
            </p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>
              <strong>Consider series advantage:</strong> First books in a series often have lower
              ROI but drive sales for later books.
            </p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>
              <strong>Factor in time:</strong> A lower ROI book that you can write quickly may
              outperform a high-ROI book that takes months.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
