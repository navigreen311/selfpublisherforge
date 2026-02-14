"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ListingAnalysisForm } from "@/modules/product-page/components/ListingAnalysisForm";
import { ListingAnalysisResults } from "@/modules/product-page/components/ListingAnalysisResults";
import { MobileCheckForm, type MobileCheckFormData } from "@/modules/product-page/components/MobileCheckForm";
import { MobileCheckResults } from "@/modules/product-page/components/MobileCheckResults";
import { BlurbGeneratorTab } from "@/modules/product-page/components/BlurbGeneratorTab";
import { KeywordOptimizerTab } from "@/modules/product-page/components/KeywordOptimizerTab";
import { APlusContentTab } from "@/modules/product-page/components/APlusContentTab";
import type { ListingAnalysisResult } from "@/modules/product-page/types";
import type { MobileCheckResult } from "@/modules/product-page/types";

export default function ProductPageLab() {
  const t = useTranslations("product-page");
  const [activeTab, setActiveTab] = useState("analyze");

  // Listing analysis state
  const [analysisResult, setAnalysisResult] = useState<ListingAnalysisResult | null>(null);

  // Mobile check state
  const [mobileResult, setMobileResult] = useState<MobileCheckResult | null>(null);
  const [mobileFormData, setMobileFormData] = useState<{
    title: string;
    author: string;
    price?: number;
  }>({ title: "", author: "" });

  const handleAnalysisComplete = (result: ListingAnalysisResult) => {
    setAnalysisResult(result);
  };

  const handleMobileCheckComplete = (result: MobileCheckResult) => {
    setMobileResult(result);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="analyze">Listing Analysis</TabsTrigger>
          <TabsTrigger value="mobile">Mobile Check</TabsTrigger>
          <TabsTrigger value="blurb">Blurb Generator</TabsTrigger>
          <TabsTrigger value="keywords">Keyword Optimizer</TabsTrigger>
          <TabsTrigger value="aplus">A+ Content</TabsTrigger>
        </TabsList>

        {/* Listing Analysis tab */}
        <TabsContent value="analyze" className="space-y-6">
          <ListingAnalysisForm onAnalysisComplete={handleAnalysisComplete} />
          {analysisResult && (
            <ListingAnalysisResults
              result={analysisResult}
              onSwitchToBlurb={() => setActiveTab("blurb")}
              onSwitchToKeywords={() => setActiveTab("keywords")}
            />
          )}
        </TabsContent>

        {/* Mobile Check tab */}
        <TabsContent value="mobile" className="space-y-6">
          <MobileCheckForm
            onCheckComplete={(result, formData) => {
              handleMobileCheckComplete(result);
              setMobileFormData(formData);
            }}
          />
          {mobileResult && (
            <MobileCheckResults
              result={mobileResult}
              title={mobileFormData.title}
              author={mobileFormData.author}
              price={mobileFormData.price}
            />
          )}
        </TabsContent>

        {/* Blurb Generator tab */}
        <TabsContent value="blurb">
          <BlurbGeneratorTab />
        </TabsContent>

        {/* Keyword Optimizer tab */}
        <TabsContent value="keywords">
          <KeywordOptimizerTab />
        </TabsContent>

        {/* A+ Content tab */}
        <TabsContent value="aplus">
          <APlusContentTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
