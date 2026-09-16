import { RotateCcw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Tag } from "../api/tags";
import { defaultTodoFilters, type TodoFilters } from "../api/todos";

interface TodoFiltersProps {
  filters: TodoFilters;
  tags: Tag[];
  onChange: (filters: TodoFilters) => void;
}

export function TodoFiltersBar({ filters, tags, onChange }: TodoFiltersProps) {
  const update = <K extends keyof TodoFilters>(
    field: K,
    value: TodoFilters[K],
  ) => onChange({ ...filters, [field]: value, page: 1 });

  return (
    <div className="space-y-3 rounded-lg border bg-muted/20 p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <div className="space-y-1 md:col-span-2">
          <Label htmlFor="todo-keyword">Keyword</Label>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              id="todo-keyword"
              className="pl-9"
              placeholder="Search title or description"
              value={filters.keyword}
              onChange={(event) => update("keyword", event.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1">
          <Label htmlFor="todo-status">Status</Label>
          <select
            id="todo-status"
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            value={filters.status}
            onChange={(event) =>
              update(
                "status",
                event.target.value as TodoFilters["status"],
              )
            }
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="space-y-1">
          <Label htmlFor="todo-tag">Tag</Label>
          <select
            id="todo-tag"
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            value={filters.tagId}
            onChange={(event) => update("tagId", event.target.value)}
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
          <Label htmlFor="todo-date-from">From date</Label>
          <Input
            id="todo-date-from"
            type="date"
            value={filters.dateFrom}
            onChange={(event) => update("dateFrom", event.target.value)}
          />
        </div>

        <div className="space-y-1">
          <Label htmlFor="todo-date-to">To date</Label>
          <Input
            id="todo-date-to"
            type="date"
            min={filters.dateFrom || undefined}
            value={filters.dateTo}
            onChange={(event) => update("dateTo", event.target.value)}
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onChange(defaultTodoFilters)}
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          Clear filters
        </Button>
      </div>
    </div>
  );
}
