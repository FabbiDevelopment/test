import { useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { Tag } from "../api/tags";
import type { Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  availableTags: Tag[];
  selected: boolean;
  onSelectedChange: (selected: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoItem({
  todo,
  availableTags,
  selected,
  onSelectedChange,
  onToggle,
  onEdit,
  onDelete,
  onAttachTag,
  onDetachTag,
}: TodoItemProps) {
  const [tagId, setTagId] = useState("");
  const unattachedTags = availableTags.filter(
    (tag) => !todo.tags.some((attached) => attached.id === tag.id),
  );

  return (
    <div className="space-y-3 rounded-lg border bg-card p-3 transition-colors hover:bg-accent/30">
      <div className="flex items-center gap-3">
        <Checkbox
          aria-label={`Select ${todo.title}`}
          checked={selected}
          onCheckedChange={(value) => onSelectedChange(value === true)}
        />

        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
        />

        <div className="min-w-0 flex-1">
          <label
            htmlFor={`todo-${todo.id}`}
            className={`cursor-pointer text-sm font-medium ${
              todo.completed ? "text-muted-foreground line-through" : ""
            }`}
          >
            {todo.title}
          </label>
          {todo.description && (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {todo.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-1">
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

      <div className="flex flex-wrap items-center gap-2 pl-14">
        {todo.tags.map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs"
            style={{ borderColor: tag.color ?? undefined }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: tag.color ?? "#64748b" }}
            />
            {tag.name}
            <button
              type="button"
              aria-label={`Remove ${tag.name} from ${todo.title}`}
              onClick={() => onDetachTag(todo.id, tag.id)}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}

        {unattachedTags.length > 0 && (
          <div className="flex items-center gap-1">
            <select
              aria-label={`Tag for ${todo.title}`}
              className="h-7 rounded-md border bg-background px-2 text-xs"
              value={tagId}
              onChange={(event) => setTagId(event.target.value)}
            >
              <option value="">Add tag…</option>
              {unattachedTags.map((tag) => (
                <option key={tag.id} value={tag.id}>
                  {tag.name}
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-7 w-7"
              aria-label={`Attach tag to ${todo.title}`}
              disabled={!tagId}
              onClick={() => {
                onAttachTag(todo.id, tagId);
                setTagId("");
              }}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
