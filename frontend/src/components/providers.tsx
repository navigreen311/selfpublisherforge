"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider, type AbstractIntlMessages } from "next-intl";
import { useState } from "react";
import { Toaster } from "sonner";

// Base messages (flat structure)
import baseMessages from "@/messages/en.json";

// Namespace-specific messages (nested structure — override base)
import adminMessages from "@/messages/en/admin.json";
import advertisingMessages from "@/messages/en/advertising.json";
import agentsMessages from "@/messages/en/agents.json";
import analyticsMessages from "@/messages/en/analytics.json";
import authMessages from "@/messages/en/auth.json";
import dashboardMessages from "@/messages/en/dashboard.json";
import homeMessages from "@/messages/en/home.json";
import knowledgeMessages from "@/messages/en/knowledge.json";
import marketMessages from "@/messages/en/market.json";
import marketingMessages from "@/messages/en/marketing.json";
import pipelineMessages from "@/messages/en/pipeline.json";
import projectsMessages from "@/messages/en/projects.json";
import publishingMessages from "@/messages/en/publishing.json";
import settingsMessages from "@/messages/en/settings.json";
import writingMessages from "@/messages/en/writing.json";
import competitorsMessages from "@/messages/en/competitors.json";
import coverDesignMessages from "@/messages/en/cover-design.json";
import onboardingMessages from "@/messages/en/onboarding.json";
import pricingMessages from "@/messages/en/pricing.json";
import productPageMessages from "@/messages/en/product-page.json";
import reviewsMessages from "@/messages/en/reviews.json";
import styleProfilesMessages from "@/messages/en/style-profiles.json";

// Deep-merge namespace files into the base messages so that
// useTranslations("dashboard") finds the correct nested keys.
const base = baseMessages as Record<string, unknown>;
const messages = {
  ...baseMessages,
  admin: adminMessages,
  advertising: { ...(base.advertising ?? {}), ...advertisingMessages },
  agents: { ...(base.agents ?? {}), ...agentsMessages },
  analytics: { ...(base.analytics ?? {}), ...analyticsMessages },
  auth: { ...(base.auth ?? {}), ...authMessages },
  competitors: competitorsMessages,
  "cover-design": coverDesignMessages,
  dashboard: dashboardMessages,
  home: homeMessages,
  knowledge: { ...(base.knowledge ?? {}), ...knowledgeMessages },
  market: { ...(base.market ?? {}), ...marketMessages },
  marketing: { ...(base.marketing ?? {}), ...marketingMessages },
  onboarding: onboardingMessages,
  pipeline: { ...(base.pipeline ?? {}), ...pipelineMessages },
  pricing: pricingMessages,
  "product-page": productPageMessages,
  projects: projectsMessages,
  publishing: { ...(base.publishing ?? {}), ...publishingMessages },
  reviews: reviewsMessages,
  settings: { ...(base.settings ?? {}), ...settingsMessages },
  "style-profiles": styleProfilesMessages,
  writing: { ...(base.writing ?? {}), ...writingMessages },
};

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 60 * 1000, retry: 1 },
        },
      })
  );

  return (
    <NextIntlClientProvider locale="en" timeZone="America/New_York" messages={messages as AbstractIntlMessages}>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="top-right" />
      </QueryClientProvider>
    </NextIntlClientProvider>
  );
}
