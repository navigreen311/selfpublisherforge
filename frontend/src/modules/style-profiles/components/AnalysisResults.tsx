"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useStyleProfile, useStyleFingerprint } from "../hooks";
import { StyleMetrics } from "./StyleMetrics";
import { VoiceCharacteristics } from "./VoiceCharacteristics";
import { SampleComparison } from "./SampleComparison";

interface AnalysisResultsProps {
  profileId: string;
  onBack: () => void;
  onSave: () => void;
}

export function AnalysisResults({ profileId, onBack, onSave }: AnalysisResultsProps) {
  const {
    data: profile,
    isLoading: profileLoading,
    refetch: refetchProfile,
  } = useStyleProfile(profileId);

  const {
    data: fingerprintData,
    isLoading: fingerprintLoading,
  } = useStyleFingerprint(profileId);

  const isAnalyzing = !profileLoading && profile?.status !== "ready";

  // Poll profile until status is 'ready'
  useEffect(() => {
    if (!isAnalyzing) return;

    const interval = setInterval(() => {
      refetchProfile();
    }, 3000);

    return () => clearInterval(interval);
  }, [isAnalyzing, refetchProfile]);

  // Loading / analyzing state
  if (profileLoading || isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent mb-4" />
        <p className="text-lg font-medium mb-1">Analyzing your writing style...</p>
        <p className="text-sm text-muted-foreground">
          This takes about 30 seconds
        </p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Profile not found.</p>
        <Button variant="outline" className="mt-4" onClick={onBack}>
          Go Back
        </Button>
      </div>
    );
  }

  const fingerprint = fingerprintData?.fingerprint;
  const styleCard = profile.style_card;

  return (
    <div className="space-y-6">
      {/* Voice Fingerprint */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-lg">Voice Fingerprint</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => {}}>
            Edit Description
          </Button>
        </CardHeader>
        <CardContent>
          {styleCard?.summary ? (
            <div className="rounded-md border p-4">
              <p className="text-sm leading-relaxed">{styleCard.summary}</p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No voice fingerprint summary available yet.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Style Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Style Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          {fingerprint ? (
            <StyleMetrics fingerprint={fingerprint} />
          ) : (
            <div className="flex flex-col items-center justify-center py-6">
              {fingerprintLoading ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-2" />
                  <p className="text-sm text-muted-foreground">Loading metrics...</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Style metrics not available.
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Voice Characteristics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Voice Characteristics</CardTitle>
        </CardHeader>
        <CardContent>
          {profile?.style_card ? (
            <VoiceCharacteristics styleCard={profile.style_card} />
          ) : (
            <div className="flex flex-col items-center justify-center py-6">
              {fingerprintLoading ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-2" />
                  <p className="text-sm text-muted-foreground">Loading characteristics...</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Voice characteristics not available.
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sample Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Sample Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <SampleComparison profileId={profileId} />
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="flex items-center justify-between border-t pt-6">
        <Button variant="outline" onClick={onBack}>
          Back to Samples
        </Button>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={onSave}>
            Save &amp; Test More
          </Button>
          <Button onClick={onSave}>
            Save Profile
          </Button>
        </div>
      </div>
    </div>
  );
}
