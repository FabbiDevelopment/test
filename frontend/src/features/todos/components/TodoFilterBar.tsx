import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "@/features/tags/api/tags";

export interface TodoFilters {
  keyword: string;
  status: string;
  tagId: string;
  dateFrom: string;
  dateTo: string;
}

interface TodoFilterBarProps {
  filters: TodoFilters;
  onChange: (filters: TodoFilters) => void;
  onOpenTagManager: () => void;
}

export function TodoFilterBar({ filters, onChange, onOpenTagManager }: TodoFilterBarProps) {
  const { data: tags = [] } = useTags();

  const handleClear = () => {
    onChange({
      keyword: "",
      status: "all",
      tagId: "all",
      dateFrom: "",
      dateTo: "",
    });
  };

  const hasActiveFilters =
    filters.keyword ||
    filters.status !== "all" ||
    filters.tagId !== "all" ||
    filters.dateFrom ||
    filters.dateTo;

  return (
    <div className="space-y-3 bg-card p-3 rounded-lg border mb-4">
      <div className="flex flex-wrap items-center gap-2">
        {/* Keyword Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search todos..."
            value={filters.keyword}
            onChange={(e) => onChange({ ...filters, keyword: e.target.value })}
            className="pl-8 text-sm h-9"
          />
        </div>

        {/* Status Select */}
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
          className="h-9 px-3 py-1 rounded-md border text-sm bg-background"
        >
          <option value="all">All Status</option>
          <option value="active">Active Only</option>
          <option value="completed">Completed Only</option>
        </select>

        {/* Tag Select */}
        <select
          value={filters.tagId}
          onChange={(e) => onChange({ ...filters, tagId: e.target.value })}
          className="h-9 px-3 py-1 rounded-md border text-sm bg-background"
        >
          <option value="all">All Tags</option>
          {tags.map((tag) => (
            <option key={tag.id} value={tag.id}>
              {tag.name}
            </option>
          ))}
        </select>

        {/* Open Tag Manager */}
        <Button variant="outline" size="sm" className="h-9" onClick={onOpenTagManager}>
          <Filter className="h-3.5 w-3.5 mr-1" /> Manage Tags
        </Button>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" className="h-9 text-xs" onClick={handleClear}>
            <X className="h-3.5 w-3.5 mr-1" /> Clear
          </Button>
        )}
      </div>

      {/* Date Range Row */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>Date from:</span>
        <Input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => onChange({ ...filters, dateFrom: e.target.value })}
          className="h-8 text-xs w-36"
        />
        <span>To:</span>
        <Input
          type="date"
          value={filters.dateTo}
          onChange={(e) => onChange({ ...filters, dateTo: e.target.value })}
          className="h-8 text-xs w-36"
        />
      </div>
    </div>
  );
}
