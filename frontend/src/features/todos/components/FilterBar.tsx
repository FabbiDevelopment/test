import React from "react";
import { Search, X, Tag as TagIcon, Filter, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTags, type Tag } from "../api/tags";
import type { TodoFilters } from "../api/todos";

interface FilterBarProps {
  filters: TodoFilters;
  onFilterChange: (filters: TodoFilters) => void;
  onOpenTagManager: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  onOpenTagManager,
}) => {
  const { data: tags = [] } = useTags();

  const handleKeywordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, keyword: e.target.value, page: 1 });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      status: e.target.value || undefined,
      page: 1,
    });
  };

  const handleTagChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      tag_id: e.target.value || undefined,
      page: 1,
    });
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      date_from: e.target.value || undefined,
      page: 1,
    });
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      date_to: e.target.value || undefined,
      page: 1,
    });
  };

  const handleClearFilters = () => {
    onFilterChange({ page: 1, size: filters.size || 20 });
  };

  const hasActiveFilters =
    !!filters.keyword ||
    !!filters.status ||
    !!filters.tag_id ||
    !!filters.date_from ||
    !!filters.date_to;

  return (
    <div className="bg-card border rounded-lg p-4 space-y-3 shadow-sm mb-6">
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search todos by title or description..."
            value={filters.keyword || ""}
            onChange={handleKeywordChange}
            className="pl-9 pr-8"
          />
          {filters.keyword && (
            <button
              onClick={() => onFilterChange({ ...filters, keyword: undefined })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Status Dropdown */}
        <div className="w-full md:w-40">
          <select
            value={filters.status || ""}
            onChange={handleStatusChange}
            className="w-full h-10 px-3 py-2 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <option value="">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="completed">Completed Only</option>
          </select>
        </div>

        {/* Tag Dropdown */}
        <div className="w-full md:w-44">
          <select
            value={filters.tag_id || ""}
            onChange={handleTagChange}
            className="w-full h-10 px-3 py-2 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <option value="">All Tags</option>
            {tags.map((tag: Tag) => (
              <option key={tag.id} value={tag.id}>
                🏷️ {tag.name}
              </option>
            ))}
          </select>
        </div>

        {/* Manage Tags Button */}
        <Button variant="outline" onClick={onOpenTagManager} className="gap-2">
          <TagIcon className="h-4 w-4" />
          Manage Tags
        </Button>
      </div>

      {/* Second Row: Date Filter & Reset */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t text-xs text-muted-foreground">
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="h-3.5 w-3.5" />
          <span>Created between:</span>
          <Input
            type="date"
            value={filters.date_from || ""}
            onChange={handleDateFromChange}
            className="h-8 text-xs w-36"
          />
          <span>to</span>
          <Input
            type="date"
            value={filters.date_to || ""}
            onChange={handleDateToChange}
            className="h-8 text-xs w-36"
          />
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="h-8 text-xs gap-1 text-destructive hover:text-destructive"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Clear All Filters
          </Button>
        )}
      </div>
    </div>
  );
};
