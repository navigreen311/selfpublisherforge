"use client";

import { useState, useMemo } from "react";
import {
  ShoppingCart, Printer, Download, Search,
  ChevronDown, ChevronRight as ChevronRightIcon,
  Leaf, Milk, Drumstick, Package, Snowflake, Croissant, CupSoda, ShoppingBag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export interface ShoppingListItem {
  name: string;
  amount: string;
  unit: string;
  category: string;
  checked: boolean;
}

interface ShoppingListProps {
  items: ShoppingListItem[];
  onToggle?: (index: number) => void;
  onPrint?: () => void;
  onExport?: () => void;
}

interface CategoryMeta { label: string; icon: typeof Leaf; badgeClass: string; }

const CATEGORIES: Record<string, CategoryMeta> = {
  Produce: { label: "Produce", icon: Leaf, badgeClass: "bg-green-100 text-green-700 border-green-200" },
  Dairy: { label: "Dairy", icon: Milk, badgeClass: "bg-blue-100 text-blue-700 border-blue-200" },
  "Meat & Seafood": { label: "Meat & Seafood", icon: Drumstick, badgeClass: "bg-red-100 text-red-700 border-red-200" },
  Pantry: { label: "Pantry", icon: Package, badgeClass: "bg-amber-100 text-amber-700 border-amber-200" },
  Frozen: { label: "Frozen", icon: Snowflake, badgeClass: "bg-cyan-100 text-cyan-700 border-cyan-200" },
  Bakery: { label: "Bakery", icon: Croissant, badgeClass: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  Beverages: { label: "Beverages", icon: CupSoda, badgeClass: "bg-purple-100 text-purple-700 border-purple-200" },
  Other: { label: "Other", icon: ShoppingBag, badgeClass: "bg-gray-100 text-gray-700 border-gray-200" },
};

const CATEGORY_ORDER = ["Produce", "Dairy", "Meat & Seafood", "Pantry", "Frozen", "Bakery", "Beverages", "Other"];

export function ShoppingList({ items, onToggle, onPrint, onExport }: ShoppingListProps) {
  const [search, setSearch] = useState("");
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  const filteredItems = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter((item) => item.name.toLowerCase().includes(q));
  }, [items, search]);

  const grouped = useMemo(() => {
    const map: Record<string, { item: ShoppingListItem; originalIndex: number }[]> = {};
    for (const cat of CATEGORY_ORDER) map[cat] = [];
    filteredItems.forEach((item) => {
      const originalIndex = items.indexOf(item);
      const cat = CATEGORY_ORDER.includes(item.category) ? item.category : "Other";
      if (!map[cat]) map[cat] = [];
      map[cat].push({ item, originalIndex });
    });
    return map;
  }, [filteredItems, items]);

  const totalItems = items.length;
  const checkedCount = items.filter((i) => i.checked).length;

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat); else next.add(cat);
      return next;
    });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <ShoppingCart className="h-4 w-4" /> Shopping List
          </CardTitle>
          <div className="flex items-center gap-2">
            {onPrint && (<Button size="sm" variant="outline" className="gap-1.5" onClick={onPrint}><Printer className="h-3.5 w-3.5" /> Print</Button>)}
            {onExport && (<Button size="sm" variant="outline" className="gap-1.5" onClick={onExport}><Download className="h-3.5 w-3.5" /> Export</Button>)}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Filter items..." className="h-8 text-sm pl-8" />
        </div>
        <Separator />
        <div className="space-y-1">
          {CATEGORY_ORDER.map((cat) => {
            const entries = grouped[cat];
            if (!entries || entries.length === 0) return null;
            const meta = CATEGORIES[cat] ?? CATEGORIES.Other;
            const Icon = meta.icon;
            const isCollapsed = collapsedCategories.has(cat);
            return (
              <div key={cat}>
                <button onClick={() => toggleCategory(cat)} className="w-full flex items-center gap-2 py-2 px-1 hover:bg-muted/50 rounded-md transition-colors">
                  {isCollapsed ? <ChevronRightIcon className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />}
                  <Icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{meta.label}</span>
                  <Badge variant="outline" className={cn("text-[10px] h-4 px-1.5 ml-auto", meta.badgeClass)}>{entries.length}</Badge>
                </button>
                {!isCollapsed && (
                  <div className="ml-6 space-y-0.5 mb-2">
                    {entries.map(({ item, originalIndex }) => (
                      <label key={originalIndex} className={cn("flex items-center gap-3 py-1.5 px-2 rounded-md hover:bg-muted/30 cursor-pointer transition-colors", item.checked && "opacity-50")}>
                        <Checkbox checked={item.checked} onCheckedChange={() => onToggle?.(originalIndex)} />
                        <span className="text-xs text-muted-foreground w-16 shrink-0">{item.amount} {item.unit}</span>
                        <span className={cn("text-sm flex-1", item.checked && "line-through text-muted-foreground")}>{item.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {filteredItems.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <ShoppingBag className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">{search ? "No items match your search" : "No items in the shopping list"}</p>
            </div>
          )}
        </div>
        <Separator />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{checkedCount} of {totalItems} items checked</span>
          <span>{totalItems - checkedCount} remaining</span>
        </div>
      </CardContent>
    </Card>
  );
}