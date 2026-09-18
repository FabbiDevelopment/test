import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTags } from "@/features/tags/api/tags";
import type { TodoFilters } from "../api/todos";

interface TodoFilterBarProps {
  filters: TodoFilters;
  onChange: (filters: TodoFilters) => void;
}

const ALL_VALUE = "__all__";

export function TodoFilterBar({ filters, onChange }: TodoFilterBarProps) {
  const { data: tags } = useTags();
  const [keywordInput, setKeywordInput] = useState(filters.keyword ?? "");

  // Debounce the free-text keyword so we don't refetch on every keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      if (keywordInput !== (filters.keyword ?? "")) {
        onChange({ ...filters, keyword: keywordInput || undefined });
      }
    }, 300);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywordInput]);

  const hasActiveFilters =
    !!filters.status ||
    !!filters.tagId ||
    !!filters.keyword ||
    !!filters.dateFrom ||
    !!filters.dateTo;

  const clearFilters = () => {
    setKeywordInput("");
    onChange({});
  };

  return (
    <div
      className="flex flex-wrap items-end gap-2 pb-2"
      data-testid="todo-filter-bar"
    >
      <div className="flex-1 min-w-[160px] space-y-1">
        <label className="text-xs text-muted-foreground" htmlFor="filter-keyword">
          Search
        </label>
        <Input
          id="filter-keyword"
          placeholder="Search title/description..."
          value={keywordInput}
          onChange={(e) => setKeywordInput(e.target.value)}
        />
      </div>

      <div className="w-36 space-y-1">
        <label className="text-xs text-muted-foreground">Status</label>
        <Select
          value={filters.status ?? ALL_VALUE}
          onValueChange={(v) =>
            onChange({
              ...filters,
              status: v === ALL_VALUE ? undefined : (v as "completed" | "active"),
            })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="w-40 space-y-1">
        <label className="text-xs text-muted-foreground">Tag</label>
        <Select
          value={filters.tagId ?? ALL_VALUE}
          onValueChange={(v) =>
            onChange({ ...filters, tagId: v === ALL_VALUE ? undefined : v })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All tags" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>All tags</SelectItem>
            {tags?.map((tag) => (
              <SelectItem key={tag.id} value={tag.id}>
                {tag.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-muted-foreground" htmlFor="filter-date-from">
          From
        </label>
        <Input
          id="filter-date-from"
          type="date"
          className="w-36"
          value={filters.dateFrom ?? ""}
          onChange={(e) =>
            onChange({ ...filters, dateFrom: e.target.value || undefined })
          }
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs text-muted-foreground" htmlFor="filter-date-to">
          To
        </label>
        <Input
          id="filter-date-to"
          type="date"
          className="w-36"
          value={filters.dateTo ?? ""}
          onChange={(e) =>
            onChange({ ...filters, dateTo: e.target.value || undefined })
          }
        />
      </div>

      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          <X className="h-3.5 w-3.5 mr-1" />
          Clear filters
        </Button>
      )}
    </div>
  );
}
