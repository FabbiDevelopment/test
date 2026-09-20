import { useEffect, useState } from "react";
import { Search, Tag as TagIcon, X, Calendar, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "@/features/tags/api/tags";
import type { TodoFilterParams } from "../api/todos";

interface TodoFilterBarProps {
  filters: TodoFilterParams;
  onFilterChange: (newFilters: Partial<TodoFilterParams>) => void;
  onResetFilters: () => void;
  onOpenTagManager: () => void;
}

export function TodoFilterBar({
  filters,
  onFilterChange,
  onResetFilters,
  onOpenTagManager,
}: TodoFilterBarProps) {
  const { data: tagsData } = useTags();
  const [searchInput, setSearchInput] = useState(filters.keyword || "");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Debounce search input (350ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== (filters.keyword || "")) {
        onFilterChange({ keyword: searchInput || undefined, page: 1 });
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput, filters.keyword, onFilterChange]);

  const hasActiveFilters = Boolean(
    filters.keyword ||
      filters.status !== undefined ||
      filters.tag_id ||
      filters.date_from ||
      filters.date_to
  );

  return (
    <div className="space-y-3 pb-4">
      {/* Primary search & quick filters */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search input */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search todos by keyword..."
            className="pl-9 pr-8 h-9 text-sm"
          />
          {searchInput && (
            <button
              onClick={() => {
                setSearchInput("");
                onFilterChange({ keyword: undefined, page: 1 });
              }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center rounded-md border p-0.5 bg-muted/40">
          <button
            type="button"
            onClick={() => onFilterChange({ status: undefined, page: 1 })}
            className={`px-3 py-1 text-xs font-medium rounded-sm transition-all ${
              filters.status === undefined
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => onFilterChange({ status: false, page: 1 })}
            className={`px-3 py-1 text-xs font-medium rounded-sm transition-all ${
              filters.status === false
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Active
          </button>
          <button
            type="button"
            onClick={() => onFilterChange({ status: true, page: 1 })}
            className={`px-3 py-1 text-xs font-medium rounded-sm transition-all ${
              filters.status === true
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Completed
          </button>
        </div>

        {/* Tag selector dropdown */}
        <div className="relative">
          <select
            value={filters.tag_id || ""}
            onChange={(e) =>
              onFilterChange({ tag_id: e.target.value || undefined, page: 1 })
            }
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring cursor-pointer"
          >
            <option value="">All Tags</option>
            {tagsData?.items.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Toggle advanced filters */}
        <Button
          variant={showAdvanced ? "secondary" : "outline"}
          size="sm"
          className="h-9 px-2.5 text-xs"
          onClick={() => setShowAdvanced(!showAdvanced)}
          title="Toggle date range filter"
        >
          <SlidersHorizontal className="h-3.5 w-3.5 mr-1" />
          Filter
        </Button>

        {/* Manage Tags modal trigger */}
        <Button
          variant="outline"
          size="sm"
          className="h-9 px-2.5 text-xs"
          onClick={onOpenTagManager}
        >
          <TagIcon className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
          Tags
        </Button>

        {/* Clear all filters */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="h-9 px-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => {
              setSearchInput("");
              onResetFilters();
            }}
          >
            <X className="h-3.5 w-3.5 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Advanced date range filters */}
      {showAdvanced && (
        <div className="flex flex-wrap items-center gap-3 p-3 rounded-md border bg-muted/20 text-xs animate-in fade-in-50">
          <div className="flex items-center gap-2">
            <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="font-medium text-muted-foreground">From:</span>
            <input
              type="date"
              value={filters.date_from ? filters.date_from.split("T")[0] : ""}
              onChange={(e) =>
                onFilterChange({
                  date_from: e.target.value
                    ? new Date(e.target.value).toISOString()
                    : undefined,
                  page: 1,
                })
              }
              className="h-8 rounded border px-2 text-xs bg-background"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="font-medium text-muted-foreground">To:</span>
            <input
              type="date"
              value={filters.date_to ? filters.date_to.split("T")[0] : ""}
              onChange={(e) =>
                onFilterChange({
                  date_to: e.target.value
                    ? new Date(e.target.value + "T23:59:59Z").toISOString()
                    : undefined,
                  page: 1,
                })
              }
              className="h-8 rounded border px-2 text-xs bg-background"
            />
          </div>
        </div>
      )}
    </div>
  );
}
