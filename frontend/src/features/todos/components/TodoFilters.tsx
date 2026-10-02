import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Tag, TodoFilters } from "../api/todos";
import {
  todoFiltersSchema,
  type TodoFiltersFormData,
} from "../schemas/todo";

interface TodoFiltersProps {
  tags: Tag[];
  filters: TodoFilters;
  onApply: (filters: TodoFilters) => void;
}

const defaultValues: TodoFiltersFormData = {
  keyword: "",
  status: "all",
  tagId: "",
  dateFrom: "",
  dateTo: "",
};

export function TodoFilters({ tags, filters, onApply }: TodoFiltersProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoFiltersFormData>({
    resolver: zodResolver(todoFiltersSchema),
    defaultValues,
  });

  useEffect(() => {
    reset({
      keyword: filters.keyword ?? "",
      status: filters.status ?? "all",
      tagId: filters.tagId ?? "",
      dateFrom: filters.dateFrom ?? "",
      dateTo: filters.dateTo ?? "",
    });
  }, [filters, reset]);

  const applyFilters = (values: TodoFiltersFormData) => {
    onApply({
      keyword: values.keyword.trim() || undefined,
      status: values.status,
      tagId: values.tagId || undefined,
      dateFrom: values.dateFrom || undefined,
      dateTo: values.dateTo || undefined,
    });
  };

  const clearFilters = () => {
    reset(defaultValues);
    onApply({ status: "all" });
  };

  return (
    <form
      onSubmit={handleSubmit(applyFilters)}
      className="space-y-3 rounded-md border p-4"
    >
      <h2 className="text-sm font-semibold">Filter todos</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="todo-keyword">Keyword</Label>
          <Input
            id="todo-keyword"
            placeholder="Search title or description"
            maxLength={200}
            {...register("keyword")}
          />
          {errors.keyword && (
            <p className="text-sm text-destructive">{errors.keyword.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-status">Status</Label>
          <select
            id="todo-status"
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("status")}
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="todo-tag">Tag</Label>
          <select
            id="todo-tag"
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
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
          <Label htmlFor="todo-date-from">Created from</Label>
          <Input id="todo-date-from" type="date" {...register("dateFrom")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="todo-date-to">Created to</Label>
          <Input id="todo-date-to" type="date" {...register("dateTo")} />
          {errors.dateTo && (
            <p className="text-sm text-destructive">{errors.dateTo.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={clearFilters}>
          Clear filters
        </Button>
        <Button type="submit">Apply filters</Button>
      </div>
    </form>
  );
}
