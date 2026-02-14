"use client";

import { useState } from "react";
import { Building2, Users, BookOpen, HardDrive } from "lucide-react";
import { useAdminOrganizations } from "../hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { OrgSettingsPanel } from "./OrgSettingsPanel";

export function OrgTable() {
  const { data: orgs, isLoading, error } = useAdminOrganizations();
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const handleManageClick = (orgId: string) => {
    setSelectedOrgId(orgId);
    setIsPanelOpen(true);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load organizations. Please try again.</p>
      </div>
    );
  }

  const getPlanBadgeVariant = (tier: string) => {
    switch (tier) {
      case "enterprise":
        return "default";
      case "pro":
        return "secondary";
      case "starter":
        return "outline";
      default:
        return "outline";
    }
  };

  const formatStorage = (bytes: number, limit: number) => {
    const usedGB = (bytes / (1024 ** 3)).toFixed(2);
    const limitGB = (limit / (1024 ** 3)).toFixed(0);
    return `${usedGB} / ${limitGB} GB`;
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {orgs?.map((org) => (
          <Card key={org.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                  <CardTitle className="text-lg">{org.name}</CardTitle>
                </div>
                <Badge variant={getPlanBadgeVariant(org.plan_tier)}>
                  {org.plan_tier.charAt(0).toUpperCase() + org.plan_tier.slice(1)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>Owner: {org.owner_name}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>{org.member_count} member{org.member_count !== 1 ? "s" : ""}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <BookOpen className="h-4 w-4" />
                  <span>{org.books_count} book{org.books_count !== 1 ? "s" : ""}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <HardDrive className="h-4 w-4" />
                  <span>{formatStorage(org.storage_used_bytes, org.storage_limit_bytes)}</span>
                </div>
                <div className="text-muted-foreground">
                  Created: {new Date(org.created_at).toLocaleDateString()}
                </div>
              </div>

              <div className="flex flex-col gap-2 pt-2">
                <Button
                  variant="default"
                  size="sm"
                  className="w-full"
                  onClick={() => handleManageClick(org.id)}
                >
                  Manage
                </Button>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm">
                    View Members
                  </Button>
                  <Button variant="outline" size="sm">
                    Usage Details
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {selectedOrgId && (
        <OrgSettingsPanel
          open={isPanelOpen}
          onOpenChange={setIsPanelOpen}
          orgId={selectedOrgId}
        />
      )}
    </>
  );
}
