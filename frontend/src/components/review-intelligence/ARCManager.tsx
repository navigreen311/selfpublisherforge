"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "@/hooks/use-translations";
import {
  useARCCampaigns,
  useSendARCReminder,
  useCreateARCCampaign,
} from "@/modules/reviews/hooks";
import type { ARCCampaign } from "@/modules/reviews/hooks";

interface ARCManagerProps {
  bookId?: string;
}

const STATUS_VARIANT: Record<ARCCampaign["status"], "default" | "secondary" | "outline"> = {
  active: "default",
  draft: "secondary",
  completed: "outline",
};

function getDaysRemaining(deadline: string | null): number | null {
  if (!deadline) return null;
  const now = new Date();
  const end = new Date(deadline);
  const diff = end.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

export function ARCManager({ bookId }: ARCManagerProps) {
  const t = useTranslations("reviews");
  const { data: campaigns, isLoading } = useARCCampaigns();
  const sendReminder = useSendARCReminder();
  const createCampaign = useCreateARCCampaign();
  const [creatingCampaign, setCreatingCampaign] = useState(false);

  const filteredCampaigns = bookId
    ? campaigns?.filter((c) => c.book_id === bookId)
    : campaigns;

  const handleSendReminder = (campaignId: string) => {
    sendReminder.mutate(campaignId);
  };

  const handleCreateCampaign = () => {
    if (!bookId) return;
    setCreatingCampaign(true);
    createCampaign.mutate(
      { book_id: bookId, name: `ARC Campaign ${new Date().toLocaleDateString()}` },
      { onSettled: () => setCreatingCampaign(false) },
    );
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {t("acquisition.arcManagement")}
          </CardTitle>
          <Button
            size="sm"
            onClick={handleCreateCampaign}
            disabled={!bookId || creatingCampaign || createCampaign.isPending}
          >
            {t("acquisition.createCampaign")}
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-md bg-muted"
              />
            ))}
          </div>
        ) : !filteredCampaigns || filteredCampaigns.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {t("acquisition.arcEmptyState")}
          </p>
        ) : (
          <div className="space-y-3">
            {filteredCampaigns.map((campaign) => {
              const daysRemaining = getDaysRemaining(campaign.deadline);
              const reviewPct =
                campaign.copies_sent > 0
                  ? Math.round(
                      (campaign.reviews_received / campaign.copies_sent) * 100,
                    )
                  : 0;

              return (
                <div
                  key={campaign.id}
                  className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  {/* Left: campaign info */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{campaign.name}</span>
                      <Badge variant={STATUS_VARIANT[campaign.status]}>
                        {t(`acquisition.status.${campaign.status}`)}
                      </Badge>
                    </div>

                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                      <span>
                        {t("acquisition.copiesSent")}: {campaign.copies_sent}
                      </span>
                      <span>
                        {t("acquisition.reviewsReceived")}: {campaign.reviews_received} ({reviewPct}%)
                      </span>
                      {campaign.deadline && (
                        <span>
                          {t("acquisition.deadline")}:{" "}
                          {new Date(campaign.deadline).toLocaleDateString()}
                          {daysRemaining !== null && (
                            <span className="ml-1">
                              ({daysRemaining > 0
                                ? t("acquisition.daysRemaining", { count: daysRemaining })
                                : t("acquisition.pastDeadline")})
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right: action buttons */}
                  <div className="flex shrink-0 items-center gap-2">
                    <Button variant="outline" size="sm">
                      {t("acquisition.viewDetails")}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleSendReminder(campaign.id)}
                      disabled={
                        sendReminder.isPending || campaign.status === "completed"
                      }
                    >
                      {t("acquisition.sendReminder")}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
