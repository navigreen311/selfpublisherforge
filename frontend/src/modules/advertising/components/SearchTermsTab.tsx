"use client";

import { useMemo } from "react";
import {
  useSearchTerms,
  useAddSearchTermAsKeyword,
  useNegateSearchTerm,
} from "../hooks";
import type { AdSearchTerm } from "../types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Plus, MinusCircle } from "lucide-react";

interface SearchTermsTabProps {
  campaignId: string;
}

function formatAcos(term: AdSearchTerm): string {
  if (term.sales === 0) {
    return term.spend > 0 ? "\u221E" : "--";
  }
  return ((term.spend / term.sales) * 100).toFixed(1) + "%";
}

function getAcosColor(term: AdSearchTerm): string {
  if (term.sales === 0) {
    return term.spend > 0 ? "text-red-600" : "text-muted-foreground";
  }
  const acos = (term.spend / term.sales) * 100;
  if (acos < 25) return "text-green-600";
  if (acos <= 40) return "text-yellow-600";
  return "text-red-600";
}

export function SearchTermsTab({ campaignId }: SearchTermsTabProps) {
  const { data: searchTerms, isLoading } = useSearchTerms(campaignId);
  const addAsKeyword = useAddSearchTermAsKeyword(campaignId);
  const negateTerm = useNegateSearchTerm(campaignId);

  // Sort by spend descending by default
  const sortedTerms = useMemo(() => {
    if (!searchTerms) return [];
    return [...searchTerms].sort((a, b) => b.spend - a.spend);
  }, [searchTerms]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-12 bg-muted rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            Search Terms ({sortedTerms.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            Actual search queries that triggered your ads. Add high-performing terms as keywords or negate irrelevant ones.
          </p>
        </div>
      </div>

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Search Term</TableHead>
              <TableHead className="text-right">Impressions</TableHead>
              <TableHead className="text-right">Clicks</TableHead>
              <TableHead className="text-right">Spend</TableHead>
              <TableHead className="text-right">Sales</TableHead>
              <TableHead className="text-right">ACOS</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedTerms.map((term) => (
              <TableRow key={term.id}>
                <TableCell className="font-medium">
                  {term.search_term}
                </TableCell>
                <TableCell className="text-right">
                  {term.impressions.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  {term.clicks.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  ${term.spend.toFixed(2)}
                </TableCell>
                <TableCell className="text-right">
                  ${term.sales.toFixed(2)}
                </TableCell>
                <TableCell className={`text-right font-medium ${getAcosColor(term)}`}>
                  {formatAcos(term)}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs text-green-700 hover:text-green-800 hover:bg-green-50"
                      onClick={() => addAsKeyword.mutate(term.id)}
                      disabled={addAsKeyword.isPending || term.action_taken === "added"}
                      title="Add as manual keyword"
                    >
                      <Plus className="h-3 w-3 mr-0.5" />
                      Add
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs text-red-700 hover:text-red-800 hover:bg-red-50"
                      onClick={() => negateTerm.mutate(term.id)}
                      disabled={negateTerm.isPending || term.action_taken === "negated"}
                      title="Add to negative keywords"
                    >
                      <MinusCircle className="h-3 w-3 mr-0.5" />
                      Negate
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {sortedTerms.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="text-center py-8 text-muted-foreground"
                >
                  No search term data available yet. Data typically appears after your campaign has been running for a few days.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
