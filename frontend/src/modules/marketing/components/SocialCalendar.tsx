"use client";

import type { SocialPost, SocialCalendar as SocialCalendarType } from "../hooks";

interface SocialCalendarProps {
  calendar?: SocialCalendarType;
  isLoading?: boolean;
  onGenerateContent?: () => void;
}

const platformIcons: Record<string, string> = {
  twitter: "X",
  facebook: "FB",
  instagram: "IG",
};

const platformColors: Record<string, string> = {
  twitter: "bg-black text-white",
  facebook: "bg-blue-600 text-white",
  instagram: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
};

const statusColors: Record<string, string> = {
  draft: "text-gray-500",
  scheduled: "text-blue-600",
  published: "text-green-600",
  failed: "text-red-600",
};

export function SocialCalendar({ calendar, isLoading, onGenerateContent }: SocialCalendarProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Not scheduled";
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-gray-200 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">
            {calendar?.total_draft || 0}
          </div>
          <div className="text-xs text-gray-500">Draft</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {calendar?.total_scheduled || 0}
          </div>
          <div className="text-xs text-gray-500">Scheduled</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {calendar?.total_published || 0}
          </div>
          <div className="text-xs text-gray-500">Published</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {calendar?.posts.length || 0}
          </div>
          <div className="text-xs text-gray-500">Total Posts</div>
        </div>
      </div>

      {/* Platform Breakdown */}
      {calendar?.platforms && Object.keys(calendar.platforms).length > 0 && (
        <div className="flex gap-3">
          {Object.entries(calendar.platforms).map(([platform, count]) => (
            <div
              key={platform}
              className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                platformColors[platform] || "bg-gray-200"
              }`}
            >
              {platformIcons[platform] || platform}: {count}
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end">
        <button
          onClick={onGenerateContent}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Generate Content with AI
        </button>
      </div>

      {/* Posts List */}
      <div className="space-y-3">
        {(!calendar?.posts || calendar.posts.length === 0) ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg">No social media posts yet.</p>
            <p className="text-sm mt-1">Generate content to get started.</p>
          </div>
        ) : (
          calendar.posts.map((post) => (
            <div key={post.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-start gap-3">
                <span
                  className={`px-2 py-1 rounded text-xs font-bold ${
                    platformColors[post.platform] || "bg-gray-200"
                  }`}
                >
                  {platformIcons[post.platform] || post.platform}
                </span>
                <div className="flex-1">
                  <p className="text-sm">{post.content}</p>
                  {post.hashtags && post.hashtags.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {post.hashtags.map((tag, i) => (
                        <span key={i} className="text-xs text-blue-500">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <span
                    className={`text-xs font-medium ${
                      statusColors[post.status] || ""
                    }`}
                  >
                    {post.status}
                  </span>
                  <div className="text-xs text-gray-400 mt-1">
                    {formatDate(post.scheduled_at)}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
