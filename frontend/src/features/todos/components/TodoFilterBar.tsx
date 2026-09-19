import { zodResolver } from "@hookform/resolvers/zod";
import { FilterX, Search } from "lucide-react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Tag } from "@/features/tags/types";
import {
  DEFAULT_TODO_FILTERS,
  type TodoFilters,
} from "../api/queryKeys";
import {
  todoFiltersSchema,
  type TodoFiltersFormData,
} from "../schemas/todo";

interface TodoFilterBarProps {
  filters: Required<TodoFilters>;
  tags: Tag[];
  onApply: (filters: Required<TodoFilters>) => void;
}

export function TodoFilterBar({ filters, tags, onApply }: TodoFilterBarProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoFiltersFormData>({
    resolver: zodResolver(todoFiltersSchema),
    values: filters,
  });

  const applyFilters = (data: TodoFiltersFormData) => {
    onApply({
      keyword: data.keyword.trim(),
      status: data.status,
      tagId: data.tagId,
      dateFrom: data.dateFrom,
      dateTo: data.dateTo,
    });
  };

  const clearFilters = () => {
    reset(DEFAULT_TODO_FILTERS);
    onApply(DEFAULT_TODO_FILTERS);
  };

  return (
    <form
      onSubmit={handleSubmit(applyFilters)}
      className="rounded-lg border bg-muted/35 p-4"
      aria-label="Filter todos"
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="space-y-1.5 lg:col-span-2">
          <Label htmlFor="todo-keyword">Find work</Label>
          <div className="relative">
            <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-muted-foreground" />
            <Input
              id="todo-keyword"
              className="pl-9"
              placeholder="Search title or details"
              {...register("keyword")}
            />
          </div>
          {errors.keyword && (
            <p className="text-xs text-destructive">{errors.keyword.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-status">Status</Label>
          <select
            id="todo-status"
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            {...register("status")}
          >
            <option value="all">All work</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-tag">Tag</Label>
          <select
            id="todo-tag"
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            {...register("tagId")}
          >
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-date-from">From</Label>
          <Input id="todo-date-from" type="date" {...register("dateFrom")} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-date-to">To</Label>
          <Input id="todo-date-to" type="date" {...register("dateTo")} />
          {errors.dateTo && (
            <p className="text-xs text-destructive">{errors.dateTo.message}</p>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={clearFilters}>
          <FilterX className="h-4 w-4" />
          Clear filters
        </Button>
        <Button type="submit" size="sm">
          Apply filters
        </Button>
      </div>
    </form>
  );
}
