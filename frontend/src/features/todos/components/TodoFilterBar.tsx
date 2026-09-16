import { useEffect, useState } from "react";
import { Search, Tag as TagIcon, X, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { TodoFilters } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";
import { useDebounce } from "@/hooks/useDebounce";

interface TodoFilterBarProps {
  filters: TodoFilters;
  onFilterChange: (filters: TodoFilters) => void;
  onOpenTagManager: () => void;
}

export function TodoFilterBar({
  filters,
  onFilterChange,
  onOpenTagManager,
}: TodoFilterBarProps) {
  const { data: tags = [] } = useTags();
  const [searchTerm, setSearchTerm] = useState(filters.keyword || "");
  const debouncedSearch = useDebounce(searchTerm, 300);

  // Sync debounced search to parent filters
  useEffect(() => {
    if (debouncedSearch !== (filters.keyword || "")) {
      onFilterChange({ ...filters, keyword: debouncedSearch });
    }
  }, [debouncedSearch]);

  // Sync external filter reset (e.g. when reset button clicked)
  useEffect(() => {
    if (!filters.keyword && searchTerm) {
      setSearchTerm("");
    }
  }, [filters.keyword]);

  const handleStatusChange = (status: "all" | "active" | "completed") => {
    onFilterChange({ ...filters, status });
  };

  const handleTagChange = (tag_id: string | undefined) => {
    onFilterChange({ ...filters, tag_id });
  };

  const handleReset = () => {
    setSearchTerm("");
    onFilterChange({ status: "all", keyword: "", tag_id: undefined });
  };

  const hasActiveFilters =
    (filters.status && filters.status !== "all") ||
    (searchTerm.trim().length > 0) ||
    Boolean(filters.tag_id);

  return (
    <div className="space-y-3 mb-4">
      {/* Search Input & Manage Tags Button */}
      <div className="flex gap-2 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search todos by title or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => {
                setSearchTerm("");
                onFilterChange({ ...filters, keyword: "" });
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onOpenTagManager}
          className="shrink-0"
        >
          <TagIcon className="h-4 w-4 mr-1.5" />
          Manage Tags
        </Button>
      </div>

      {/* Filter controls: Status buttons & Tag pills */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        {/* Status segment buttons */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border">
          <Button
            type="button"
            variant={!filters.status || filters.status === "all" ? "default" : "ghost"}
            size="sm"
            className="h-7 text-xs px-3"
            onClick={() => handleStatusChange("all")}
          >
            All
          </Button>
          <Button
            type="button"
            variant={filters.status === "active" ? "default" : "ghost"}
            size="sm"
            className="h-7 text-xs px-3"
            onClick={() => handleStatusChange("active")}
          >
            Active
          </Button>
          <Button
            type="button"
            variant={filters.status === "completed" ? "default" : "ghost"}
            size="sm"
            className="h-7 text-xs px-3"
            onClick={() => handleStatusChange("completed")}
          >
            Completed
          </Button>
        </div>

        {/* Tag filter pills */}
        {tags.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Filter className="h-3 w-3" />
              Tag:
            </span>
            <Button
              type="button"
              variant={!filters.tag_id ? "secondary" : "ghost"}
              size="sm"
              className="h-6 text-xs px-2"
              onClick={() => handleTagChange(undefined)}
            >
              All Tags
            </Button>
            {tags.map((tag) => {
              const isSelected = filters.tag_id === tag.id;
              return (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => handleTagChange(isSelected ? undefined : tag.id)}
                  className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full border transition-all ${
                    isSelected
                      ? "ring-2 ring-primary ring-offset-1 font-semibold"
                      : "opacity-80 hover:opacity-100"
                  }`}
                  style={{
                    backgroundColor: `${tag.color || "#6366f1"}1a`,
                    borderColor: tag.color || "#6366f1",
                    color: tag.color || "#6366f1",
                  }}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: tag.color || "#6366f1" }}
                  />
                  {tag.name}
                </button>
              );
            })}
          </div>
        )}

        {/* Reset button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="h-7 text-xs text-muted-foreground hover:text-foreground"
          >
            Clear Filters
          </Button>
        )}
      </div>
    </div>
  );
}
