import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "@/features/tags/api/tags";
import type { TodoFilters } from "../api/todos";

interface TodoFilterBarProps {
  filters: TodoFilters;
  onFilterChange: (filters: TodoFilters) => void;
  onReset: () => void;
}

export function TodoFilterBar({
  filters,
  onFilterChange,
  onReset,
}: TodoFilterBarProps) {
  const { data: tags = [] } = useTags();

  const hasActiveFilters = Boolean(
    filters.keyword ||
      filters.status !== undefined ||
      filters.tag_id ||
      filters.date_from ||
      filters.date_to
  );

  return (
    <div className="space-y-3 p-3 rounded-lg border bg-card/60 backdrop-blur-sm mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          <Filter className="h-3.5 w-3.5" />
          Filter & Search
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="h-6 px-2 text-xs text-muted-foreground hover:text-destructive"
          >
            <X className="h-3 w-3 mr-1" />
            Clear Filters
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
        {/* Keyword Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search todos..."
            value={filters.keyword || ""}
            onChange={(e) =>
              onFilterChange({ ...filters, keyword: e.target.value || undefined, page: 1 })
            }
            className="pl-8 h-9 text-sm"
          />
        </div>

        {/* Status Dropdown */}
        <div>
          <select
            value={filters.status === undefined ? "" : String(filters.status)}
            onChange={(e) => {
              const val = e.target.value;
              onFilterChange({
                ...filters,
                status: val === "" ? undefined : val === "true",
                page: 1,
              });
            }}
            className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">All Statuses</option>
            <option value="false">Active (Pending)</option>
            <option value="true">Completed</option>
          </select>
        </div>

        {/* Tag Dropdown */}
        <div>
          <select
            value={filters.tag_id || ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                tag_id: e.target.value || undefined,
                page: 1,
              })
            }
            className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">All Tags</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                🏷️ {tag.name}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range */}
        <div className="flex items-center gap-1.5">
          <Input
            type="date"
            placeholder="From"
            value={filters.date_from || ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                date_from: e.target.value || undefined,
                page: 1,
              })
            }
            className="h-9 text-xs px-2"
          />
          <span className="text-muted-foreground text-xs">-</span>
          <Input
            type="date"
            placeholder="To"
            value={filters.date_to || ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                date_to: e.target.value || undefined,
                page: 1,
              })
            }
            className="h-9 text-xs px-2"
          />
        </div>
      </div>
    </div>
  );
}
