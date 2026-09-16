import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { TodoFilters } from "../api/todos";
import { useTags } from "../../tags/api/tags";

interface TodoFilterBarProps {
  filters: TodoFilters;
  onFiltersChange: (filters: TodoFilters) => void;
}

export function TodoFilterBar({ filters, onFiltersChange }: TodoFilterBarProps) {
  const { data: tags = [] } = useTags();
  const [keyword, setKeyword] = useState(filters.keyword || "");

  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, keyword: keyword || undefined, page: 1 });
    }, 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  const updateFilter = (key: keyof TodoFilters, value: string) => {
    onFiltersChange({ ...filters, [key]: value || undefined, page: 1 });
  };

  const clearFilters = () => {
    setKeyword("");
    onFiltersChange({});
  };

  const hasActiveFilters = Object.values(filters).some(val => val !== undefined && val !== "");

  return (
    <div className="flex flex-col gap-3 p-4 bg-card border-b">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search todos..."
            className="pl-8"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </div>
        <select
          className="h-10 px-3 py-2 text-sm rounded-md border border-input bg-background ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={filters.status || ""}
          onChange={(e) => updateFilter("status", e.target.value)}
        >
          <option value="">All Status</option>
          <option value="false">Active</option>
          <option value="true">Completed</option>
        </select>
        <select
          className="h-10 px-3 py-2 text-sm rounded-md border border-input bg-background ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={filters.tag_id || ""}
          onChange={(e) => updateFilter("tag_id", e.target.value)}
        >
          <option value="">All Tags</option>
          {tags.map(tag => (
            <option key={tag.id} value={tag.id}>{tag.name}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1">
          <span className="text-sm text-muted-foreground">From:</span>
          <Input
            type="date"
            className="h-9 w-auto"
            value={filters.date_from || ""}
            onChange={(e) => updateFilter("date_from", e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-sm text-muted-foreground">To:</span>
          <Input
            type="date"
            className="h-9 w-auto"
            value={filters.date_to || ""}
            onChange={(e) => updateFilter("date_to", e.target.value)}
          />
        </div>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto text-muted-foreground">
            <X className="h-4 w-4 mr-1" /> Clear
          </Button>
        )}
      </div>
    </div>
  );
}
