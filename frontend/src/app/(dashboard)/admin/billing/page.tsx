
"use client";

import { DollarSign, TrendingUp, CreditCard, Users } from "lucide-react";
import { usePlatformStats, useAdminOrgs } from "@/modules/admin/hooks";
import { StatCard } from "@/components/shared/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "@/hooks/use-translations";

export default function AdminBillingPage() {
  const t = useTranslations("admin");
  const { data: stats, isLoading: statsLoading } = usePlatformStats();
  const { data: orgsData, isLoading: orgsLoading } = useAdminOrgs(
    { subscription_status: "active" },
    1,
    10
  );

  const calculateARR = (mrr: number) => (mrr * 12) / 100;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold text-foreground">{t("billing.title")}</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("billing.subtitle")}
        </p>
      </div>

      {/* Revenue Stats */}
      <section>
        <h3 className="text-lg font-semibold text-foreground mb-4">{t("billing.revenueMetrics")}</h3>
        {statsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-card rounded-lg border p-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-32" />
              </div>
            ))}
          </div>
        ) : stats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label={t("billing.mrr")}
              value={`$${(stats.mrr / 100).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`}
              icon={DollarSign}
            />
            <StatCard
              label={t("billing.arr")}
              value={`$${calculateARR(stats.mrr).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`}
              icon={TrendingUp}
            />
            <StatCard
              label={t("billing.activeSubscriptions")}
              value={stats.active_subscriptions.toLocaleString()}
              icon={CreditCard}
            />
            <StatCard
              label={t("billing.payingCustomers")}
              value={stats.active_organizations.toLocaleString()}
              icon={Users}
            />
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
            <p className="text-red-800">{t("billing.failedToLoadStats")}</p>
          </div>
        )}
      </section>

      {/* Top Paying Organizations */}
      <section>
        <h3 className="text-lg font-semibold text-foreground mb-4">
          {t("billing.topPayingOrganizations")}
        </h3>
        {orgsLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : orgsData && orgsData.items.length > 0 ? (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("billing.organization")}</TableHead>
                  <TableHead>{t("billing.plan")}</TableHead>
                  <TableHead>{t("billing.members")}</TableHead>
                  <TableHead>{t("billing.status")}</TableHead>
                  <TableHead className="text-right">{t("billing.mrr")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orgsData.items
                  .sort((a, b) => b.mrr - a.mrr)
                  .slice(0, 10)
                  .map((org) => (
                    <TableRow key={org.id}>
                      <TableCell className="font-medium">{org.name}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            org.plan_tier === "enterprise"
                              ? "default"
                              : org.plan_tier === "pro"
                                ? "secondary"
                                : "outline"
                          }
                        >
                          {org.plan_tier.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>{org.member_count}</TableCell>
                      <TableCell>
                        {org.subscription_status ? (
                          <Badge
                            variant={
                              org.subscription_status === "active"
                                ? "default"
                                : org.subscription_status === "past_due"
                                  ? "destructive"
                                  : "secondary"
                            }
                          >
                            {org.subscription_status}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        ${(org.mrr / 100).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="border rounded-lg p-8 text-center text-muted-foreground">
            {t("billing.noPayingOrgs")}
          </div>
        )}
      </section>
    </div>
  );
}
