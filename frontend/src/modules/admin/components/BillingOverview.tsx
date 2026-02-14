"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAdminBilling } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Download } from "lucide-react";

export function BillingOverview() {
  const { data: billing, isLoading, error } = useAdminBilling();

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load billing information. Please try again.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!billing) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No billing information available
      </div>
    );
  }

  const calculatePercentage = (used: number, limit: number) => {
    if (limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 ** 3);
    return gb.toFixed(2);
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    } else if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return "bg-red-500";
    if (percentage >= 75) return "bg-yellow-500";
    return "bg-primary";
  };

  return (
    <div className="space-y-6">
      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-2xl font-bold">
                {billing.plan_name} · ${(billing.plan_price / 100).toFixed(2)}/month
              </p>
              {billing.next_billing && (
                <p className="text-sm text-muted-foreground">
                  Renews {new Date(billing.next_billing).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage This Month */}
      <Card>
        <CardHeader>
          <CardTitle>Usage This Month</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* AI Tokens */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">AI Tokens</span>
              <span className="text-muted-foreground">
                {formatTokens(billing.usage.tokens.used)} / {formatTokens(billing.usage.tokens.limit)}
              </span>
            </div>
            <Progress
              value={calculatePercentage(billing.usage.tokens.used, billing.usage.tokens.limit)}
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              {calculatePercentage(billing.usage.tokens.used, billing.usage.tokens.limit).toFixed(1)}% used
            </p>
          </div>

          {/* Storage */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Storage</span>
              <span className="text-muted-foreground">
                {formatBytes(billing.usage.storage.used)} GB / {formatBytes(billing.usage.storage.limit)} GB
              </span>
            </div>
            <Progress
              value={calculatePercentage(billing.usage.storage.used, billing.usage.storage.limit)}
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              {calculatePercentage(billing.usage.storage.used, billing.usage.storage.limit).toFixed(1)}% used
            </p>
          </div>

          {/* Users */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Users</span>
              <span className="text-muted-foreground">
                {billing.usage.users.used} / {billing.usage.users.limit}
              </span>
            </div>
            <Progress
              value={calculatePercentage(billing.usage.users.used, billing.usage.users.limit)}
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              {calculatePercentage(billing.usage.users.used, billing.usage.users.limit).toFixed(1)}% used
            </p>
          </div>

          {/* Books */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Books</span>
              <span className="text-muted-foreground">
                {billing.usage.books.used} / {billing.usage.books.limit}
              </span>
            </div>
            <Progress
              value={calculatePercentage(billing.usage.books.used, billing.usage.books.limit)}
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              {calculatePercentage(billing.usage.books.used, billing.usage.books.limit).toFixed(1)}% used
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Invoice History */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
        </CardHeader>
        <CardContent>
          {billing.invoices.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No invoices available
            </p>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {billing.invoices.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell>
                        {new Date(invoice.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{invoice.description}</TableCell>
                      <TableCell>
                        ${(invoice.amount / 100).toFixed(2)}
                      </TableCell>
                      <TableCell>
                        {invoice.status === "paid" ? (
                          <Badge variant="default">
                            <span className="mr-1">✅</span> Paid
                          </Badge>
                        ) : invoice.status === "pending" ? (
                          <Badge variant="secondary">Pending</Badge>
                        ) : (
                          <Badge variant="destructive">Failed</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {invoice.pdf_url && (
                          <Button
                            variant="ghost"
                            size="sm"
                            asChild
                          >
                            <a href={invoice.pdf_url} download>
                              <Download className="h-4 w-4 mr-1" />
                              Download PDF
                            </a>
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button variant="default">Upgrade Plan</Button>
        <Button variant="outline">Update Payment Method</Button>
        <Button variant="outline">Cancel Subscription</Button>
      </div>
    </div>
  );
}
