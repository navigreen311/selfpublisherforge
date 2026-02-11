"use client";

import { type AudiencePersona } from "../hooks";

interface AudienceDNAProps {
  personas: AudiencePersona[];
}

export function AudienceDNA({ personas }: AudienceDNAProps) {
  if (!personas || personas.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Audience DNA</h3>
        <p className="text-gray-500 text-center py-8">No audience data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Audience Composition</h3>
        <p className="text-sm text-gray-500 mb-4">Reader personas based on market analysis</p>

        {/* Persona Breakdown */}
        <div className="space-y-2 mb-6">
          {personas.map((persona) => (
            <div key={persona.persona_id}>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-900">{persona.name}</span>
                <span className="text-gray-600">{persona.percentage_of_audience.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${persona.percentage_of_audience}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Personas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {personas.map((persona) => (
          <div key={persona.persona_id} className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <h4 className="text-lg font-semibold text-gray-900">{persona.name}</h4>
              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {persona.percentage_of_audience.toFixed(0)}%
              </span>
            </div>

            <p className="text-sm text-gray-600 mb-4">{persona.description}</p>

            <div className="space-y-3">
              {/* Demographics */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Demographics</p>
                <div className="flex gap-4 text-sm">
                  <span className="text-gray-900">
                    <span className="font-medium">Age:</span> {persona.age_range}
                  </span>
                  <span className="text-gray-900">
                    <span className="font-medium">Gender:</span> {persona.gender_skew}
                  </span>
                </div>
              </div>

              {/* Reading Habits */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Reading Habits</p>
                <div className="text-sm text-gray-900">
                  <span className="font-medium">Frequency:</span> {persona.reading_frequency}
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {persona.preferred_formats.map((format) => (
                    <span
                      key={format}
                      className="inline-flex px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700 capitalize"
                    >
                      {format}
                    </span>
                  ))}
                </div>
              </div>

              {/* Price Sensitivity */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Price Sensitivity</p>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full capitalize ${
                  persona.price_sensitivity === "low"
                    ? "bg-green-100 text-green-800"
                    : persona.price_sensitivity === "high"
                    ? "bg-red-100 text-red-800"
                    : "bg-yellow-100 text-yellow-800"
                }`}>
                  {persona.price_sensitivity}
                </span>
              </div>

              {/* Discovery Channels */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">How They Find Books</p>
                <div className="flex flex-wrap gap-1">
                  {persona.discovery_channels.map((channel) => (
                    <span
                      key={channel}
                      className="inline-flex px-2 py-0.5 text-xs rounded bg-blue-50 text-blue-700"
                    >
                      {channel.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>

              {/* Motivations */}
              {persona.motivations.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Motivations</p>
                  <ul className="text-sm text-gray-700 space-y-0.5">
                    {persona.motivations.slice(0, 3).map((motivation, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-blue-600 mr-1">•</span>
                        <span>{motivation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Favorite Authors */}
              {persona.favorite_authors.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Favorite Authors</p>
                  <p className="text-sm text-gray-700">
                    {persona.favorite_authors.slice(0, 3).join(", ")}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
