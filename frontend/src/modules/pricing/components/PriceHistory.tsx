"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useProjects } from "@/modules/projects/hooks";
import { usePriceHistory } from "../hooks";

// Colors for multi-book lines
const BOOK_COLORS = [
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#9333ea",
  "#ea580c",
  "#0891b2",
  "#ca8a04",
  "#e11d48",
];

interface ChangeLogEntry {
  date: string;
  book: string;
  old: number;
  new: number;
  reason: string;
  impact: number;
}

const MOCK_CHANGE_LOG: ChangeLogEntry[] = [
  { date: "2026-02-08", book: "Digital Marketing", old: 9.99, new: 4.99, reason: "Promo", impact: 12.5 },
  { date: "2026-02-05", book: "JavaScript Patterns", old: 2.99, new: 3.99, reason: "Strategy", impact: 8.3 },
  { date: "2026-02-01", book: "Romance Rockies", old: 4.99, new: 0.99, reason: "Launch", impact: -15.2 },
  { date: "2026-01-20", book: "Keto Guide", old: 7.99, new: 9.99, reason: "Value", impact: 5.1 },
];

function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getReasonVariant(reason: string): "default" | "secondary" | "outline" | "destructive" {
  switch (reason.toLowerCase()) {
    case "promo":
      return "destructive";
    case "launch":
      return "default";
    case "strategy":
      return "secondary";
    default:
      return "outline";
  }
}

export function PriceHistory() {
  const [selectedBook, setSelectedBook] = useState<string>("all");

  // Fetch projects (books) for the filter dropdown
  const { data: projects } = useProjects();

  // Fetch price history from API (filtered by book if selected)
  const bookIdFilter = selectedBook !== "all" ? selectedBook : undefined;
  const { data: historyData } = usePriceHistory(bookIdFilter);

  // Build the change log from API data or fall back to mock
  const changeLog = useMemo<ChangeLogEntry[]>(() => {
    if (historyData && historyData.length > 0) {
      return historyData
        .filter((entry) => entry.old_price !== undefined)
        .map((entry) => {
          const bookTitle =
            projects?.find((p) => p.id === entry.book_id)?.title ?? entry.book_id;
          return {
            date: entry.created_at,
            book: bookTitle,
            old: entry.old_price ?? 0,
            new: entry.new_price,
            reason: entry.reason ?? "Update",
            impact: entry.revenue_impact_pct ?? 0,
          };
        })
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
    return MOCK_CHANGE_LOG;
  }, [historyData, projects]);

  // Build chart data: group by date, one line per book
  const { chartData, bookNames } = useMemo(() => {
    const entries = changeLog;
    const names = Array.from(new Set(entries.map((e) => e.book)));

    // Build timeline points from the change log
    const dateMap = new Map<string, Record<string, number>>();

    for (const entry of entries) {
      const dateKey = entry.date.slice(0, 10);
      if (!dateMap.has(dateKey)) {
        dateMap.set(dateKey, {});
      }
      const record = dateMap.get(dateKey)!;
      record[entry.book] = entry.new;
    }

    // Sort by date ascending
    const sortedDates = Array.from(dateMap.keys()).sort();
    const data = sortedDates.map((dateKey) => ({
      date: dateKey,
      ...dateMap.get(dateKey),
    }));

    return { chartData: data, bookNames: names };
  }, [changeLog]);

  // Filter bookNames if a specific book is selected
  const visibleBooks = useMemo(() => {
    if (selectedBook === "all") return bookNames;
    const selectedTitle = projects?.find((p) => p.id === selectedBook)?.title;
    if (selectedTitle && bookNames.includes(selectedTitle)) {
      return [selectedTitle];
    }
    return bookNames;
  }, [selectedBook, bookNames, projects]);

  // Summary stats from change log
  const allPrices = changeLog.flatMap((e) => [e.old, e.new]).filter((p) => p > 0);
  const lowestPrice = allPrices.length > 0 ? Math.min(...allPrices) : 0;
  const highestPrice = allPrices.length > 0 ? Math.max(...allPrices) : 0;
  const currentPrice = changeLog.length > 0 ? changeLog[0].new : 0;
  const priceChanges = changeLog.length;

  return (
    <div className="space-y-6">
      {/* Book Filter */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Price Change History</h3>
          <Select value={selectedBook} onValueChange={setSelectedBook}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Filter by book" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Books</SelectItem>
              {projects?.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Price Timeline Chart */}
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatShortDate(value)}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value}`}
                label={{ value: "Price ($)", angle: -90, position: "insideLeft" }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload || !payload.length) return null;
                  return (
                    <div className="bg-background border rounded-lg shadow-lg p-3">
                      <p className="font-medium mb-1">{formatShortDate(label)}</p>
                      {payload.map((entry, idx) => (
                        <p key={idx} className="text-sm" style={{ color: entry.color }}>
                          {entry.name}: <span className="font-medium">${Number(entry.value).toFixed(2)}</span>
                        </p>
                      ))}
                    </div>
                  );
                }}
              />
              <Legend />
              {visibleBooks.map((bookName, idx) => (
                <Line
                  key={bookName}
                  type="monotone"
                  dataKey={bookName}
                  stroke={BOOK_COLORS[idx % BOOK_COLORS.length]}
                  strokeWidth={2}
                  dot={{ fill: BOOK_COLORS[idx % BOOK_COLORS.length], r: 4 }}
                  name={bookName}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-muted-foreground text-center py-8">No price history available</p>
        )}

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">${lowestPrice.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">Lowest Price</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">${highestPrice.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">Highest Price</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">${currentPrice.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">Current Price</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{priceChanges}</div>
            <div className="text-xs text-muted-foreground">Price Changes</div>
          </div>
        </div>
      </Card>

      {/* Change Log Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Change Log</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Book</TableHead>
              <TableHead className="text-right">Old Price</TableHead>
              <TableHead className="text-right">New Price</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead className="text-right">Revenue Impact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {changeLog.length > 0 ? (
              changeLog.map((entry, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-medium">
                    {formatShortDate(entry.date)}
                  </TableCell>
                  <TableCell>{entry.book}</TableCell>
                  <TableCell className="text-right">${entry.old.toFixed(2)}</TableCell>
                  <TableCell className="text-right">${entry.new.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={getReasonVariant(entry.reason)}>
                      {entry.reason}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        entry.impact >= 0
                          ? "text-green-600 font-medium"
                          : "text-red-600 font-medium"
                      }
                    >
                      {entry.impact >= 0 ? "+" : ""}
                      {entry.impact.toFixed(1)}%
                    </span>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                  No price changes recorded
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
