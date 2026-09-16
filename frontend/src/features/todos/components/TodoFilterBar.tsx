import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Tag } from "@/features/tags/api/tags";
import type { TodoFilters } from "../api/todos";

interface TodoFilterBarProps {
  filters: TodoFilters;
  tags: Tag[];
  onChange: (next: TodoFilters) => void;
  onClear: () => void;
}

const EMPTY_FILTERS: TodoFilters = {
  status: "",
  tag_id: "",
  keyword: "",
  date_from: "",
  date_to: "",
};

/** THÊM: Filter bar — keyword, status, tag, date range, clear filters (Level 4 UI) */
export function TodoFilterBar({
  filters,
  tags,
  onChange,
  onClear,
}: TodoFilterBarProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 mb-4 p-3 rounded-lg border bg-muted/20">
      <div className="space-y-1">
        <Label htmlFor="filter-keyword">Keyword</Label>
        <Input
          id="filter-keyword"
          placeholder="Search title or description..."
          value={filters.keyword ?? ""}
          onChange={(e) => onChange({ ...filters, keyword: e.target.value })}
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="filter-status">Status</Label>
        <select
          id="filter-status"
          className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={filters.status ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              status: e.target.value as TodoFilters["status"],
            })
          }
        >
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      <div className="space-y-1">
        <Label htmlFor="filter-tag">Tag</Label>
        <select
          id="filter-tag"
          className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={filters.tag_id ?? ""}
          onChange={(e) => onChange({ ...filters, tag_id: e.target.value })}
        >
          <option value="">All tags</option>
          {tags.map((tag) => (
            <option key={tag.id} value={tag.id}>
              {tag.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <Label htmlFor="filter-from">Date from</Label>
        <Input
          id="filter-from"
          type="date"
          value={filters.date_from ?? ""}
          onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="filter-to">Date to</Label>
        <Input
          id="filter-to"
          type="date"
          value={filters.date_to ?? ""}
          onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
        />
      </div>

      <div className="flex items-end">
        <Button type="button" variant="outline" onClick={() => onClear()}>
          Clear filters
        </Button>
      </div>
    </div>
  );
}

export { EMPTY_FILTERS };
