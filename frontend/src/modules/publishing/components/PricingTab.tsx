"use client";

import { useState, useMemo } from "react";
import { useBooks } from "@/modules/writing/hooks";
import { useBookMetadata } from "../hooks";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DollarSign,
  Calculator,
  TrendingUp,
  BarChart3,
  History,
  Save,
} from "lucide-react";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Royalty calculation helpers
// ---------------------------------------------------------------------------

const PRINT_COST_PER_PAGE = 0.012;
const PAPERBACK_BASE_COST = 0.85;
const HARDCOVER_BASE_COST = 5.5;
const PRINT_ROYALTY_RATE = 0.6;
const AUDIOBOOK_ROYALTY_RATE = 0.4;
const KINDLE_HIGH_ROYALTY = 0.7;
const KINDLE_LOW_ROYALTY = 0.35;
const KINDLE_MIN_PRICE_FOR_HIGH = 2.99;
const KINDLE_MAX_PRICE_FOR_HIGH = 9.99;
const MONTHLY_SALES_PROJECTION = 100;

function getKindleRoyaltyRate(price: number): number {
  if (price >= KINDLE_MIN_PRICE_FOR_HIGH && price <= KINDLE_MAX_PRICE_FOR_HIGH) {
    return KINDLE_HIGH_ROYALTY;
  }
  return KINDLE_LOW_ROYALTY;
}

function calcPrintCost(pageCount: number, baseCost: number): number {
  return pageCount * PRINT_COST_PER_PAGE + baseCost;
}

function calcPrintRoyalty(price: number, printCost: number): number {
  const net = price - printCost;
  return net > 0 ? net * PRINT_ROYALTY_RATE : 0;
}

interface FormatPricing {
  price: string;
  printCost: number;
  royaltyRate: number;
  royalty: number;
}

function computeFormat(
  priceStr: string,
  pageCount: number,
  type: "kindle" | "paperback" | "hardcover" | "audiobook"
): FormatPricing {
  const price = parseFloat(priceStr) || 0;

  switch (type) {
    case "kindle": {
      const rate = getKindleRoyaltyRate(price);
      return {
        price: priceStr,
        printCost: 0,
        royaltyRate: rate,
        royalty: price * rate,
      };
    }
    case "paperback": {
      const cost = calcPrintCost(pageCount, PAPERBACK_BASE_COST);
      return {
        price: priceStr,
        printCost: cost,
        royaltyRate: PRINT_ROYALTY_RATE,
        royalty: calcPrintRoyalty(price, cost),
      };
    }
    case "hardcover": {
      const cost = calcPrintCost(pageCount, HARDCOVER_BASE_COST);
      return {
        price: priceStr,
        printCost: cost,
        royaltyRate: PRINT_ROYALTY_RATE,
        royalty: calcPrintRoyalty(price, cost),
      };
    }
    case "audiobook":
      return {
        price: priceStr,
        printCost: 0,
        royaltyRate: AUDIOBOOK_ROYALTY_RATE,
        royalty: price * AUDIOBOOK_ROYALTY_RATE,
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PricingTab() {
  const { data: books, isLoading: booksLoading } = useBooks();
  const [selectedBookId, setSelectedBookId] = useState<string>("");

  const { data: metadata } = useBookMetadata(selectedBookId);

  const pageCount = metadata?.page_count ?? 250;

  // Format price inputs
  const [kindlePrice, setKindlePrice] = useState("4.99");
  const [paperbackPrice, setPaperbackPrice] = useState("14.99");
  const [hardcoverPrice, setHardcoverPrice] = useState("24.99");
  const [audiobookPrice, setAudiobookPrice] = useState("19.99");

  // Compute royalties
  const formats = useMemo(() => {
    return {
      kindle: computeFormat(kindlePrice, pageCount, "kindle"),
      paperback: computeFormat(paperbackPrice, pageCount, "paperback"),
      hardcover: computeFormat(hardcoverPrice, pageCount, "hardcover"),
      audiobook: computeFormat(audiobookPrice, pageCount, "audiobook"),
    };
  }, [kindlePrice, paperbackPrice, hardcoverPrice, audiobookPrice, pageCount]);

  const totalMonthlyRevenue = useMemo(() => {
    return (
      (formats.kindle.royalty +
        formats.paperback.royalty +
        formats.hardcover.royalty +
        formats.audiobook.royalty) *
      MONTHLY_SALES_PROJECTION
    );
  }, [formats]);

  const fmt = (n: number) => `$${n.toFixed(2)}`;
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`;

  return (
    <div className="space-y-6">
      {/* Book Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <DollarSign className="h-5 w-5" />
            Pricing & Royalty Calculator
          </CardTitle>
          <CardDescription>
            Calculate royalties across formats and project monthly revenue
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-w-sm">
            <Label htmlFor="book-select">Select Book</Label>
            <Select
              value={selectedBookId}
              onValueChange={setSelectedBookId}
            >
              <SelectTrigger id="book-select" className="mt-1.5">
                <SelectValue placeholder={booksLoading ? "Loading books..." : "Choose a book"} />
              </SelectTrigger>
              <SelectContent>
                {books?.map((book) => (
                  <SelectItem key={book.id} value={book.id}>
                    {book.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedBookId && metadata && (
              <p className="mt-2 text-sm text-muted-foreground">
                Page count: {pageCount} pages
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Royalty Calculator Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Calculator className="h-5 w-5" />
            Royalty Calculator
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Format</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Print Cost</TableHead>
                <TableHead>Royalty %</TableHead>
                <TableHead>Your Royalty</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Kindle */}
              <TableRow>
                <TableCell className="font-medium">Kindle</TableCell>
                <TableCell>
                  <div className="w-28">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={kindlePrice}
                      onChange={(e) => setKindlePrice(e.target.value)}
                      className="h-9"
                    />
                  </div>
                  {(parseFloat(kindlePrice) < KINDLE_MIN_PRICE_FOR_HIGH ||
                    parseFloat(kindlePrice) > KINDLE_MAX_PRICE_FOR_HIGH) &&
                    parseFloat(kindlePrice) > 0 && (
                      <p className="text-xs text-amber-600 mt-1">
                        35% rate (price outside $2.99–$9.99)
                      </p>
                    )}
                </TableCell>
                <TableCell className="text-muted-foreground">—</TableCell>
                <TableCell>{pct(formats.kindle.royaltyRate)}</TableCell>
                <TableCell className="font-semibold text-green-700">
                  {fmt(formats.kindle.royalty)}
                </TableCell>
              </TableRow>

              {/* Paperback */}
              <TableRow>
                <TableCell className="font-medium">Paperback</TableCell>
                <TableCell>
                  <div className="w-28">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={paperbackPrice}
                      onChange={(e) => setPaperbackPrice(e.target.value)}
                      className="h-9"
                    />
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {fmt(formats.paperback.printCost)}
                </TableCell>
                <TableCell>{pct(formats.paperback.royaltyRate)}</TableCell>
                <TableCell className="font-semibold text-green-700">
                  {fmt(formats.paperback.royalty)}
                </TableCell>
              </TableRow>

              {/* Hardcover */}
              <TableRow>
                <TableCell className="font-medium">Hardcover</TableCell>
                <TableCell>
                  <div className="w-28">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={hardcoverPrice}
                      onChange={(e) => setHardcoverPrice(e.target.value)}
                      className="h-9"
                    />
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {fmt(formats.hardcover.printCost)}
                </TableCell>
                <TableCell>{pct(formats.hardcover.royaltyRate)}</TableCell>
                <TableCell className="font-semibold text-green-700">
                  {fmt(formats.hardcover.royalty)}
                </TableCell>
              </TableRow>

              {/* Audiobook */}
              <TableRow>
                <TableCell className="font-medium">Audiobook</TableCell>
                <TableCell>
                  <div className="w-28">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={audiobookPrice}
                      onChange={(e) => setAudiobookPrice(e.target.value)}
                      className="h-9"
                    />
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">—</TableCell>
                <TableCell>{pct(formats.audiobook.royaltyRate)}</TableCell>
                <TableCell className="font-semibold text-green-700">
                  {fmt(formats.audiobook.royalty)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Revenue Projection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5" />
            Revenue Projection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted/50 p-4">
            <p className="text-sm text-muted-foreground">
              At {MONTHLY_SALES_PROJECTION} sales/month per format:
            </p>
            <p className="mt-1 text-2xl font-bold text-green-700">
              {fmt(totalMonthlyRevenue)}/mo across all formats
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Kindle</p>
                <p className="font-medium">
                  {fmt(formats.kindle.royalty * MONTHLY_SALES_PROJECTION)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Paperback</p>
                <p className="font-medium">
                  {fmt(formats.paperback.royalty * MONTHLY_SALES_PROJECTION)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Hardcover</p>
                <p className="font-medium">
                  {fmt(formats.hardcover.royalty * MONTHLY_SALES_PROJECTION)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Audiobook</p>
                <p className="font-medium">
                  {fmt(formats.audiobook.royalty * MONTHLY_SALES_PROJECTION)}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Competitor Price Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5" />
            Competitor Price Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed border-muted-foreground/30 p-8 text-center">
            <BarChart3 className="mx-auto h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm text-muted-foreground">
              Competitor data from Market Research module
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <Button
          onClick={() => toast.info("Price update is not yet implemented")}
        >
          <Save className="mr-2 h-4 w-4" />
          Update Prices
        </Button>
        <Button
          variant="outline"
          onClick={() => toast.info("Price history is not yet implemented")}
        >
          <History className="mr-2 h-4 w-4" />
          Price History
        </Button>
      </div>
    </div>
  );
}
