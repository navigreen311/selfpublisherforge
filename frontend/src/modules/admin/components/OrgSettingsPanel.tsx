"use client";

import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useAdminOrgDetail, useUpdateAdminOrg } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";

interface OrgSettingsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  orgId: string;
}

export function OrgSettingsPanel({ open, onOpenChange, orgId }: OrgSettingsPanelProps) {
  const { data: org, isLoading } = useAdminOrgDetail(orgId);
  const updateOrg = useUpdateAdminOrg();
  const { toast } = useToast();

  const [name, setName] = useState("");
  const [featureToggles, setFeatureToggles] = useState<Record<string, boolean>>({
    ai_agents: false,
    cover_design_ai: false,
    voice_forge: false,
    advertising_intelligence: false,
    pricing_automation: false,
  });

  useEffect(() => {
    if (org) {
      setName(org.name);
      setFeatureToggles({
        ai_agents: org.feature_toggles?.ai_agents ?? false,
        cover_design_ai: org.feature_toggles?.cover_design_ai ?? false,
        voice_forge: org.feature_toggles?.voice_forge ?? false,
        advertising_intelligence: org.feature_toggles?.advertising_intelligence ?? false,
        pricing_automation: org.feature_toggles?.pricing_automation ?? false,
      });
    }
  }, [org]);

  const handleToggleFeature = (feature: string, checked: boolean) => {
    setFeatureToggles((prev) => ({
      ...prev,
      [feature]: checked,
    }));
  };

  const handleSave = async () => {
    try {
      await updateOrg.mutateAsync({
        orgId,
        data: {
          name,
          feature_toggles: featureToggles,
        },
      });
      toast({
        title: "Success",
        description: "Organization settings updated successfully.",
      });
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update organization settings.",
        variant: "destructive",
      });
    }
  };

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

  const getPlanLimits = (tier: string) => {
    switch (tier) {
      case "enterprise":
        return "Unlimited books, 1 TB storage, 50 users";
      case "pro":
        return "50 books, 100 GB storage, 10 users";
      case "starter":
        return "20 books, 10 GB storage, 5 users";
      default:
        return "5 books, 1 GB storage, 1 user";
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Organization Settings</SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <div className="space-y-4 mt-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : org ? (
          <div className="space-y-6 mt-6">
            {/* Organization Name */}
            <div className="space-y-2">
              <Label htmlFor="org-name">Organization Name</Label>
              <Input
                id="org-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter organization name"
              />
            </div>

            {/* Plan Display */}
            <div className="space-y-2">
              <Label>Current Plan</Label>
              <div className="flex items-center gap-2">
                <Badge variant={getPlanBadgeVariant(org.plan_tier)}>
                  {org.plan_tier.charAt(0).toUpperCase() + org.plan_tier.slice(1)}
                </Badge>
              </div>
            </div>

            {/* Plan Limits */}
            <div className="space-y-2">
              <Label>Plan Limits</Label>
              <p className="text-sm text-muted-foreground">
                {getPlanLimits(org.plan_tier)}
              </p>
            </div>

            {/* Feature Toggles */}
            <div className="space-y-3">
              <Label>Feature Toggles</Label>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="ai-agents"
                    checked={featureToggles.ai_agents}
                    onCheckedChange={(checked) =>
                      handleToggleFeature("ai_agents", checked as boolean)
                    }
                  />
                  <label
                    htmlFor="ai-agents"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    AI Agents
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="cover-design-ai"
                    checked={featureToggles.cover_design_ai}
                    onCheckedChange={(checked) =>
                      handleToggleFeature("cover_design_ai", checked as boolean)
                    }
                  />
                  <label
                    htmlFor="cover-design-ai"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Cover Design AI
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="voice-forge"
                    checked={featureToggles.voice_forge}
                    onCheckedChange={(checked) =>
                      handleToggleFeature("voice_forge", checked as boolean)
                    }
                  />
                  <label
                    htmlFor="voice-forge"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    VoiceForge
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="advertising-intelligence"
                    checked={featureToggles.advertising_intelligence}
                    onCheckedChange={(checked) =>
                      handleToggleFeature("advertising_intelligence", checked as boolean)
                    }
                  />
                  <label
                    htmlFor="advertising-intelligence"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Advertising Intelligence
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="pricing-automation"
                    checked={featureToggles.pricing_automation}
                    onCheckedChange={(checked) =>
                      handleToggleFeature("pricing_automation", checked as boolean)
                    }
                  />
                  <label
                    htmlFor="pricing-automation"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Pricing Automation
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2 pt-4">
              <Button
                onClick={handleSave}
                disabled={updateOrg.isPending}
                className="w-full"
              >
                {updateOrg.isPending ? "Saving..." : "Save"}
              </Button>
              <Button variant="outline" className="w-full">
                Upgrade Plan
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            Organization not found
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
