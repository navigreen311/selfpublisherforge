"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PriceSimulator } from "@/modules/pricing/components/PriceSimulator";
import { KUCalculator } from "@/modules/pricing/components/KUCalculator";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function PriceSimulatorPage() {
  const t = useTranslations("pricing");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("simulator.title")}</h1>
          <p className="text-muted-foreground mt-1">
            {t("simulator.subtitle")}
          </p>
        </div>
        <Link href="/pricing">
          <Button variant="outline">{t("simulator.backToDashboard")}</Button>
        </Link>
      </div>

      {/* Tabs for different calculators */}
      <Tabs defaultValue="simulator" className="space-y-6">
        <TabsList>
          <TabsTrigger value="simulator">{t("simulator.priceSimulator")}</TabsTrigger>
          <TabsTrigger value="ku-calculator">{t("simulator.kuCalculator")}</TabsTrigger>
        </TabsList>

        <TabsContent value="simulator">
          <PriceSimulator />
        </TabsContent>

        <TabsContent value="ku-calculator">
          <KUCalculator />
        </TabsContent>
      </Tabs>
    </div>
  );
}
