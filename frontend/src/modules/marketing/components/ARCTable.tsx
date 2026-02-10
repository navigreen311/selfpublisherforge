"use client";

import type { ARCCampaign, ARCRecipient } from "../hooks";

interface ARCTableProps {
  campaigns: ARCCampaign[];
  isLoading?: boolean;
  onCreateCampaign?: () => void;
  onSendCopies?: (campaignId: string) => void;
  onViewCampaign?: (campaignId: string) => void;
}

const statusBadge: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-blue-100 text-blue-700",
  sending: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  archived: "bg-red-100 text-red-700",
};

const recipientStatusBadge: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  sent: "bg-blue-100 text-blue-600",
  delivered: "bg-indigo-100 text-indigo-600",
  reviewed: "bg-green-100 text-green-600",
  failed: "bg-red-100 text-red-600",
};

export function ARCTable({
  campaigns,
  isLoading,
  onCreateCampaign,
  onSendCopies,
  onViewCampaign,
}: ARCTableProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-200 rounded" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">ARC Campaigns</h2>
        <button
          onClick={onCreateCampaign}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          New ARC Campaign
        </button>
      </div>

      {/* Table */}
      {campaigns.length === 0 ? (
        <div className="text-center py-12 text-gray-400 border rounded-lg">
          <p className="text-lg">No ARC campaigns yet.</p>
          <p className="text-sm mt-1">Create your first campaign to start sending review copies.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse" aria-label="ARC campaigns">
            <thead>
              <tr className="bg-gray-50 text-left text-sm text-gray-500">
                <th scope="col" className="p-3 font-medium">Campaign</th>
                <th scope="col" className="p-3 font-medium">Status</th>
                <th scope="col" className="p-3 font-medium text-center">Total</th>
                <th scope="col" className="p-3 font-medium text-center">Sent</th>
                <th scope="col" className="p-3 font-medium text-center">Reviews</th>
                <th scope="col" className="p-3 font-medium">Deadline</th>
                <th scope="col" className="p-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {campaigns.map((campaign) => {
                const reviewRate =
                  campaign.sent_copies > 0
                    ? Math.round(
                        (campaign.reviews_received / campaign.sent_copies) * 100
                      )
                    : 0;

                return (
                  <tr
                    key={campaign.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => onViewCampaign?.(campaign.id)}
                  >
                    <td className="p-3">
                      <div className="font-medium">{campaign.name}</div>
                      {campaign.description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {campaign.description}
                        </div>
                      )}
                    </td>
                    <td className="p-3">
                      <span
                        className={`text-xs px-2 py-1 rounded-full font-medium ${
                          statusBadge[campaign.status] || ""
                        }`}
                      >
                        {campaign.status}
                      </span>
                    </td>
                    <td className="p-3 text-center font-medium">
                      {campaign.total_copies}
                    </td>
                    <td className="p-3 text-center font-medium">
                      {campaign.sent_copies}
                    </td>
                    <td className="p-3 text-center">
                      <span className="font-medium">{campaign.reviews_received}</span>
                      <span className="text-xs text-gray-400 ml-1">({reviewRate}%)</span>
                    </td>
                    <td className="p-3 text-sm text-gray-600">
                      {formatDate(campaign.deadline)}
                    </td>
                    <td className="p-3">
                      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                        {campaign.status === "draft" && (
                          <button
                            onClick={() => onSendCopies?.(campaign.id)}
                            aria-label={`Send copies for ${campaign.name}`}
                            className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                          >
                            Send
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
