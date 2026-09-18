import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Tag, TodoFilters } from "../api/todos";
import { defaultTodoFilters } from "../api/todos";

interface Props {
  filters: TodoFilters;
  tags: Tag[];
  onChange: (filters: TodoFilters) => void;
}

export function TodoFilterBar({ filters, tags, onChange }: Props) {
  const update = (patch: Partial<TodoFilters>) =>
    onChange({ ...filters, ...patch, page: 1 });

  return (
    <div className="grid gap-2 md:grid-cols-3 mb-4" aria-label="Todo filters">
      <Input
        aria-label="Search todos"
        placeholder="Search title or description"
        value={filters.keyword}
        onChange={(event) => update({ keyword: event.target.value })}
      />
      <select
        aria-label="Status filter"
        className="h-9 rounded-md border bg-transparent px-3 text-sm"
        value={filters.status}
        onChange={(event) =>
          update({ status: event.target.value as TodoFilters["status"] })
        }
      >
        <option value="all">All statuses</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
      </select>
      <select
        aria-label="Tag filter"
        className="h-9 rounded-md border bg-transparent px-3 text-sm"
        value={filters.tag_id}
        onChange={(event) => update({ tag_id: event.target.value })}
      >
        <option value="">All tags</option>
        {tags.map((tag) => (
          <option key={tag.id} value={tag.id}>{tag.name}</option>
        ))}
      </select>
      <Input
        aria-label="Created from"
        type="date"
        value={filters.date_from}
        onChange={(event) => update({ date_from: event.target.value })}
      />
      <Input
        aria-label="Created to"
        type="date"
        value={filters.date_to}
        onChange={(event) => update({ date_to: event.target.value })}
      />
      <Button variant="outline" onClick={() => onChange(defaultTodoFilters)}>
        Clear filters
      </Button>
    </div>
  );
}
