"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StrategyCards } from "./StrategyCards";
import { PriceHistory } from "./PriceHistory";
import { RoyaltyBreakdown } from "./RoyaltyBreakdown";
import Link from "next/link";

export function PricingDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Pricing Automation</h1>
          <p className="text-muted-foreground mt-1">
            Optimize your book prices to maximize royalties and sales
          </p>
        </div>
        <Link href="/pricing/simulator">
          <Button>Price Simulator</Button>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Active Rules</div>
          <div className="text-2xl font-bold mt-1">3</div>
          <div className="text-xs text-muted-foreground mt-1">Across 12 books</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Avg. Price</div>
          <div className="text-2xl font-bold mt-1">$4.27</div>
          <div className="text-xs text-green-600 mt-1">+5.2% vs. last month</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Avg. Royalty Rate</div>
          <div className="text-2xl font-bold mt-1">68%</div>
          <div className="text-xs text-muted-foreground mt-1">Weighted by revenue</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Next Price Change</div>
          <div className="text-2xl font-bold mt-1">3</div>
          <div className="text-xs text-muted-foreground mt-1">Scheduled this week</div>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="history">Price History</TabsTrigger>
          <TabsTrigger value="analysis">Royalty Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Strategies Overview */}
          <StrategyCards />

          {/* Recent Activity */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Price Changes</h3>
            <div className="space-y-3">
              {MOCK_RECENT_CHANGES.map((change, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div>
                    <div className="font-medium">{change.bookTitle}</div>
                    <div className="text-sm text-muted-foreground">{change.date}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      ${change.oldPrice.toFixed(2)} → ${change.newPrice.toFixed(2)}
                    </div>
                    <div
                      className={`text-sm ${change.impact >= 0 ? "text-green-600" : "text-red-600"}`}
                    >
                      {change.impact >= 0 ? "+" : ""}
                      {change.impact.toFixed(1)}% revenue
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-6">
          <StrategyCards />

          {/* Strategy Recommendations */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
            <div className="space-y-4">
              {MOCK_RECOMMENDATIONS.map((rec, idx) => (
                <div key={idx} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-medium">{rec.title}</div>
                      <div className="text-sm text-muted-foreground mt-1">{rec.description}</div>
                    </div>
                    <Button variant="outline" size="sm">
                      Apply
                    </Button>
                  </div>
                  <div className="mt-2 text-sm">
                    <span className="text-muted-foreground">Expected impact:</span>{" "}
                    <span className="font-medium text-green-600">{rec.impact}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <PriceHistory />
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          <RoyaltyBreakdown />

          {/* Competitor Pricing */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Competitive Price Analysis</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Compare your pricing against similar books in your genre
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Market Average</div>
                <div className="text-2xl font-bold mt-1">$3.99</div>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Your Average</div>
                <div className="text-2xl font-bold mt-1">$4.27</div>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Recommendation</div>
                <div className="text-2xl font-bold mt-1">$3.99</div>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Mock data
const MOCK_RECENT_CHANGES = [
  {
    bookTitle: "The Digital Marketing Handbook",
    date: "2024-02-08",
    oldPrice: 9.99,
    newPrice: 4.99,
    impact: 12.5,
  },
  {
    bookTitle: "JavaScript Patterns for Beginners",
    date: "2024-02-05",
    oldPrice: 2.99,
    newPrice: 3.99,
    impact: 8.3,
  },
  {
    bookTitle: "Romance in the Rockies",
    date: "2024-02-01",
    oldPrice: 4.99,
    newPrice: 0.99,
    impact: -15.2,
  },
];

const MOCK_RECOMMENDATIONS = [
  {
    title: "Increase price during promotional boost",
    description:
      "Your book 'The Digital Marketing Handbook' is getting organic traffic. Consider raising price from $4.99 to $5.99.",
    impact: "+$145/month estimated",
  },
  {
    title: "Test competitive pricing",
    description:
      "Similar books in your genre are priced at $3.99. A/B test this price point against your current $4.99.",
    impact: "+22% sales volume",
  },
  {
    title: "Schedule end-of-month promotion",
    description:
      "Historical data shows strong sales during month-end. Schedule a 48-hour price drop to $0.99.",
    impact: "+350 downloads",
  },
];
