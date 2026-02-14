"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { usePricingRules } from "../hooks";
import { PricingStrategyType, RuleStatus } from "../types";
import { StrategySetupDialog } from "./StrategySetupDialog";

const STRATEGY_INFO = {
  [PricingStrategyType.COMPETITIVE_MATCH]: {
    title: "Competitive Match",
    description: "Price based on competitor analysis to stay competitive in your market.",
    color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    icon: "📊",
  },
  [PricingStrategyType.VALUE_BASED]: {
    title: "Value-Based",
    description: "Price based on perceived value and quality of your content.",
    color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    icon: "💎",
  },
  [PricingStrategyType.PENETRATION]: {
    title: "Penetration",
    description: "Lower prices to gain market share and build readership quickly.",
    color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    icon: "🎯",
  },
  [PricingStrategyType.DYNAMIC]: {
    title: "Dynamic",
    description: "Automatically adjust prices based on demand, competition, and sales data.",
    color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    icon: "⚡",
  },
  [PricingStrategyType.PROMOTIONAL]: {
    title: "Promotional",
    description: "Temporary price reductions for launches, holidays, or marketing campaigns.",
    color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    icon: "🎉",
  },
};

export function StrategyCards() {
  const { data: rulesData, isLoading } = usePricingRules({ status: RuleStatus.ACTIVE });
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [selectedStrategyType, setSelectedStrategyType] =
    useState<PricingStrategyType>(PricingStrategyType.COMPETITIVE_MATCH);

  function handleSetupStrategy(strategy: PricingStrategyType) {
    setSelectedStrategyType(strategy);
    setSetupDialogOpen(true);
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6 animate-pulse">
            <div className="h-4 bg-muted rounded w-3/4 mb-2" />
            <div className="h-3 bg-muted rounded w-full mb-4" />
            <div className="h-8 bg-muted rounded w-1/2" />
          </Card>
        ))}
      </div>
    );
  }

  const activeRules = rulesData?.items || [];
  const currentStrategy = activeRules[0]?.strategy || null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Pricing Strategies</h2>
        {currentStrategy && (
          <Badge className="text-sm">
            Current: {STRATEGY_INFO[currentStrategy]?.title || currentStrategy}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(STRATEGY_INFO).map(([strategy, info]) => {
          const isActive = currentStrategy === strategy;
          const activeRule = activeRules.find((r) => r.strategy === strategy);

          return (
            <StrategyCard
              key={strategy}
              strategy={strategy as PricingStrategyType}
              info={info}
              isActive={isActive}
              activeRule={activeRule}
              onSetup={() => handleSetupStrategy(strategy as PricingStrategyType)}
            />
          );
        })}
      </div>

      {/* Active Rules Summary */}
      {activeRules.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Active Pricing Rules</h3>
          <div className="space-y-3">
            {activeRules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between p-3 bg-muted rounded-lg"
              >
                <div className="flex-1">
                  <div className="font-medium">{rule.name}</div>
                  {rule.description && (
                    <div className="text-sm text-muted-foreground">{rule.description}</div>
                  )}
                </div>
                <div className="text-right ml-4">
                  <div className="text-sm font-medium">
                    ${rule.min_price.toFixed(2)} - ${rule.max_price.toFixed(2)}
                  </div>
                  {rule.target_price && (
                    <div className="text-xs text-muted-foreground">
                      Target: ${rule.target_price.toFixed(2)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <StrategySetupDialog
        open={setupDialogOpen}
        onOpenChange={setSetupDialogOpen}
        strategyType={selectedStrategyType}
      />
    </div>
  );
}

interface StrategyCardProps {
  strategy: PricingStrategyType;
  info: {
    title: string;
    description: string;
    color: string;
    icon: string;
  };
  isActive: boolean;
  activeRule?: {
    id: string;
    name: string;
    min_price: number;
    max_price: number;
    target_price?: number;
  };
  onSetup: () => void;
}

function StrategyCard({ info, isActive, activeRule, onSetup }: StrategyCardProps) {
  return (
    <Card className={`p-6 ${isActive ? "ring-2 ring-primary" : ""}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="text-3xl">{info.icon}</div>
        {isActive && <Badge variant="default">Active</Badge>}
      </div>

      <h3 className="font-semibold mb-2">{info.title}</h3>
      <p className="text-sm text-muted-foreground mb-4">{info.description}</p>

      {activeRule ? (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Price Range</div>
          <div className="font-medium">
            ${activeRule.min_price.toFixed(2)} - ${activeRule.max_price.toFixed(2)}
          </div>
          {activeRule.target_price && (
            <div className="text-sm text-muted-foreground">
              Target: ${activeRule.target_price.toFixed(2)}
            </div>
          )}
        </div>
      ) : (
        <Button variant="outline" size="sm" className="w-full" onClick={onSetup}>
          Set Up Strategy
        </Button>
      )}
    </Card>
  );
}
