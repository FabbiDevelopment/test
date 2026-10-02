import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Plus, Trash2 } from "lucide-react";
import type { Tag, Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  tags: Tag[];
  selected: boolean;
  onToggle: (todo: Todo) => void;
  onSelect: (todoId: string, selected: boolean) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoItem({
  todo,
  tags,
  selected,
  onToggle,
  onSelect,
  onEdit,
  onDelete,
  onAttachTag,
  onDetachTag,
}: TodoItemProps) {
  const todoTags = todo.tags ?? [];
  const unassignedTags = tags.filter(
    (tag) => !todoTags.some((todoTag) => todoTag.id === tag.id)
  );

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      <Checkbox
        aria-label={`Select ${todo.title}`}
        checked={selected}
        onCheckedChange={(checked) => onSelect(todo.id, checked === true)}
      />
      <Checkbox
        id={`todo-${todo.id}`}
        aria-label={todo.title}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
      />

      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer ${
            todo.completed ? "line-through text-muted-foreground" : ""
          }`}
        >
          {todo.title}
        </label>
        {todo.description && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            {todo.description}
          </p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {todoTags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs"
              style={{
                borderColor: tag.color ?? undefined,
                color: tag.color ?? undefined,
              }}
            >
              {tag.name}
              <button
                type="button"
                aria-label={`Remove ${tag.name} from ${todo.title}`}
                className="font-bold"
                onClick={() => onDetachTag(todo.id, tag.id)}
              >
                ×
              </button>
            </span>
          ))}
          {unassignedTags.length > 0 && (
            <label className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Plus className="size-3" aria-hidden="true" />
              <span className="sr-only">Add tag to {todo.title}</span>
              <select
                aria-label={`Add tag to ${todo.title}`}
                className="h-7 max-w-36 rounded border bg-background px-2"
                value=""
                onChange={(event) => {
                  if (event.target.value) {
                    onAttachTag(todo.id, event.target.value);
                  }
                }}
              >
                <option value="">Add tag</option>
                {unassignedTags.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.name}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          aria-label={`Edit ${todo.title}`}
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          aria-label={`Delete ${todo.title}`}
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
