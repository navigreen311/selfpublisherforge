"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  searchPlaceholder: string;
  onSearch: (query: string) => void;
  statusOptions?: FilterOption[];
  onStatusChange?: (status: string) => void;
  sortOptions?: FilterOption[];
  onSortChange?: (sort: string) => void;
  initialStatus?: string;
  initialSort?: string;
}

export const DEFAULT_STATUS_OPTIONS: FilterOption[] = [
  { label: "All Statuses", value: "all" },
  { label: "Draft", value: "draft" },
  { label: "In Progress", value: "in_progress" },
  { label: "Published", value: "published" },
];

export const DEFAULT_SORT_OPTIONS: FilterOption[] = [
  { label: "Recently Updated", value: "updated_desc" },
  { label: "Title A-Z", value: "title_asc" },
  { label: "Title Z-A", value: "title_desc" },
  { label: "Date Created", value: "created_desc" },
];

/**
 * FilterBar — shared search + status + sort toolbar for landing pages.
 *
 * Per Phase 1.2 of the platform spec. Replaces empty/unlabeled dropdowns
 * across Children's, Coloring, Puzzle, Comic, Cookbook, and Style Profile
 * landings.
 */
export function FilterBar({
  searchPlaceholder,
  onSearch,
  statusOptions = DEFAULT_STATUS_OPTIONS,
  onStatusChange,
  sortOptions = DEFAULT_SORT_OPTIONS,
  onSortChange,
  initialStatus = "all",
  initialSort = "updated_desc",
}: FilterBarProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState(initialStatus);
  const [sort, setSort] = useState(initialSort);

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={searchPlaceholder}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            onSearch(e.target.value);
          }}
          className="pl-9"
          aria-label="Search"
        />
      </div>

      {onStatusChange && (
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v);
            onStatusChange(v);
          }}
        >
          <SelectTrigger className="w-[180px]" aria-label="Filter by status">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {onSortChange && (
        <Select
          value={sort}
          onValueChange={(v) => {
            setSort(v);
            onSortChange(v);
          }}
        >
          <SelectTrigger className="w-[200px]" aria-label="Sort by">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            {sortOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}

export default FilterBar;
