"use client";

import { type NicheSeasonality, type SeasonalEvent } from "../hooks";

interface SeasonalCalendarProps {
  seasonality: NicheSeasonality;
}

export function SeasonalCalendar({ seasonality }: SeasonalCalendarProps) {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const getMonthDemandColor = (demand: number) => {
    if (demand >= 1.2) return "bg-green-100 border-green-300 text-green-900";
    if (demand >= 0.8) return "bg-blue-50 border-blue-200 text-blue-900";
    return "bg-gray-50 border-gray-200 text-gray-700";
  };

  const getMonthDemandLabel = (demand: number) => {
    if (demand >= 1.2) return "Peak";
    if (demand >= 0.8) return "Normal";
    return "Low";
  };

  return (
    <div className="space-y-6">
      {/* Genre Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 capitalize">{seasonality.genre} Seasonality</h3>
        <p className="text-sm text-gray-500 mt-1">
          Demand patterns and best launch windows for this genre
        </p>
      </div>

      {/* Monthly Demand Calendar */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h4 className="text-base font-semibold text-gray-900 mb-4">Monthly Demand Index</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {months.map((month) => {
            const demand = seasonality.monthly_demand[month] || 1.0;
            const isPeak = seasonality.peak_months.includes(month);
            const isLow = seasonality.low_months.includes(month);

            return (
              <div
                key={month}
                className={`border-2 rounded-lg p-3 ${getMonthDemandColor(demand)} ${
                  isPeak ? "ring-2 ring-green-500" : isLow ? "ring-2 ring-red-300" : ""
                }`}
              >
                <p className="text-xs font-semibold uppercase">{month.substring(0, 3)}</p>
                <p className="text-2xl font-bold mt-1">{(demand * 100).toFixed(0)}</p>
                <p className="text-xs mt-1">{getMonthDemandLabel(demand)}</p>
              </div>
            );
          })}
        </div>
        <div className="flex justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 ring-2 ring-green-500 bg-green-100"></div>
            <span className="text-gray-600">Peak Months</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 ring-2 ring-red-300 bg-gray-50"></div>
            <span className="text-gray-600">Low Months</span>
          </div>
        </div>
      </div>

      {/* Launch Windows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Best Launch Windows */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h4 className="text-base font-semibold text-gray-900 mb-4">
            Best Launch Windows
          </h4>
          {seasonality.best_launch_windows.length > 0 ? (
            <div className="space-y-3">
              {seasonality.best_launch_windows.map((window, idx) => (
                <div key={idx} className="border-l-4 border-green-500 bg-green-50 p-3 rounded-r">
                  <p className="text-sm font-semibold text-gray-900">
                    {window.start_month} - {window.end_month}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">{window.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No specific launch windows identified</p>
          )}
        </div>

        {/* Avoid Windows */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h4 className="text-base font-semibold text-gray-900 mb-4">
            Windows to Avoid
          </h4>
          {seasonality.avoid_windows.length > 0 ? (
            <div className="space-y-3">
              {seasonality.avoid_windows.map((window, idx) => (
                <div key={idx} className="border-l-4 border-red-500 bg-red-50 p-3 rounded-r">
                  <p className="text-sm font-semibold text-gray-900">
                    {window.start_month} - {window.end_month}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">{window.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No specific windows to avoid</p>
          )}
        </div>
      </div>

      {/* Seasonal Events */}
      {seasonality.seasonal_events.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h4 className="text-base font-semibold text-gray-900 mb-4">Seasonal Events & Triggers</h4>
          <div className="space-y-4">
            {seasonality.seasonal_events.map((event) => (
              <SeasonalEventCard key={event.event_id} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SeasonalEventCard({ event }: { event: SeasonalEvent }) {
  const impactColor =
    event.impact_level === "high"
      ? "bg-purple-100 text-purple-800 border-purple-300"
      : event.impact_level === "medium"
      ? "bg-blue-100 text-blue-800 border-blue-300"
      : "bg-gray-100 text-gray-800 border-gray-300";

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h5 className="text-sm font-semibold text-gray-900">{event.name}</h5>
          <p className="text-xs text-gray-500">
            {new Date(event.start_date).toLocaleDateString()} - {new Date(event.end_date).toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-2">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded border capitalize ${impactColor}`}>
            {event.impact_level}
          </span>
          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800 border border-yellow-300">
            {event.demand_multiplier}x
          </span>
        </div>
      </div>

      <p className="text-sm text-gray-700 mb-3">{event.description}</p>

      {event.genres_affected.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Affected Genres</p>
          <div className="flex flex-wrap gap-1">
            {event.genres_affected.map((genre) => (
              <span
                key={genre}
                className="inline-flex px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700 capitalize"
              >
                {genre}
              </span>
            ))}
          </div>
        </div>
      )}

      {event.recommendations.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Recommendations</p>
          <ul className="space-y-0.5">
            {event.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start text-xs text-gray-700">
                <span className="text-blue-600 mr-1">→</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
