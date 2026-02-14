"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowUpDown } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface CampaignRow {
  campaign_id: string;
  name: string;
  spend: number;
  sales: number;
  acos: number;
  impressions: number;
  clicks: number;
  ctr: number;
}

type SortField = "name" | "spend" | "sales" | "acos" | "impressions" | "ctr";
type SortDirection = "asc" | "desc";

interface TopCampaignsTableProps {
  campaigns: CampaignRow[];
}

function getAcosColor(acos: number): string {
  if (acos < 25) return "text-green-600";
  if (acos <= 40) return "text-yellow-600";
  return "text-red-600";
}

export function TopCampaignsTable({ campaigns }: TopCampaignsTableProps) {
  const router = useRouter();
  const [sortField, setSortField] = useState<SortField>("spend");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const sortedCampaigns = useMemo(() => {
    return [...campaigns].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      const multiplier = sortDirection === "asc" ? 1 : -1;

      if (typeof aVal === "string" && typeof bVal === "string") {
        return aVal.localeCompare(bVal) * multiplier;
      }
      return ((aVal as number) - (bVal as number)) * multiplier;
    });
  }, [campaigns, sortField, sortDirection]);

  const SortableHeader = ({
    field,
    children,
  }: {
    field: SortField;
    children: React.ReactNode;
  }) => (
    <TableHead
      className="cursor-pointer select-none hover:text-foreground"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        <ArrowUpDown className="h-3 w-3" />
        {sortField === field && (
          <span className="text-xs">
            {sortDirection === "asc" ? "\u2191" : "\u2193"}
          </span>
        )}
      </div>
    </TableHead>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Top Campaigns</CardTitle>
      </CardHeader>
      <CardContent>
        {campaigns.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No campaign data available
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <SortableHeader field="name">Campaign Name</SortableHeader>
                <SortableHeader field="spend">Spend</SortableHeader>
                <SortableHeader field="sales">Sales</SortableHeader>
                <SortableHeader field="acos">ACOS</SortableHeader>
                <SortableHeader field="impressions">Impressions</SortableHeader>
                <SortableHeader field="ctr">CTR</SortableHeader>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCampaigns.map((campaign) => (
                <TableRow
                  key={campaign.campaign_id}
                  className="cursor-pointer"
                  onClick={() =>
                    router.push(
                      `/advertising/campaigns/${campaign.campaign_id}`
                    )
                  }
                >
                  <TableCell className="font-medium">
                    {campaign.name}
                  </TableCell>
                  <TableCell>${campaign.spend.toFixed(2)}</TableCell>
                  <TableCell>${campaign.sales.toFixed(2)}</TableCell>
                  <TableCell className={getAcosColor(campaign.acos)}>
                    {campaign.acos.toFixed(1)}%
                  </TableCell>
                  <TableCell>
                    {campaign.impressions.toLocaleString()}
                  </TableCell>
                  <TableCell>{campaign.ctr.toFixed(2)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
