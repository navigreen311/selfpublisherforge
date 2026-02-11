"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PriceSimulator } from "@/modules/pricing/components/PriceSimulator";
import { KUCalculator } from "@/modules/pricing/components/KUCalculator";
import Link from "next/link";

export default function PriceSimulatorPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Pricing Tools</h1>
          <p className="text-muted-foreground mt-1">
            Interactive calculators to optimize your book pricing and revenue
          </p>
        </div>
        <Link href="/pricing">
          <Button variant="outline">Back to Dashboard</Button>
        </Link>
      </div>

      {/* Tabs for different calculators */}
      <Tabs defaultValue="simulator" className="space-y-6">
        <TabsList>
          <TabsTrigger value="simulator">Price Simulator</TabsTrigger>
          <TabsTrigger value="ku-calculator">KU Calculator</TabsTrigger>
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
