import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, X, Plus } from "lucide-react";
import type { Todo } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";
import { useAttachTag, useDetachTag } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({
  todo,
  isSelected,
  onSelect,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const { data: tags } = useTags();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  const availableTags = tags?.filter(
    (t) => !todo.tags?.find((attached) => attached.id === t.id)
  );

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/10 transition-colors group">
      {onSelect && (
        <Checkbox
          checked={isSelected}
          onCheckedChange={(c) => onSelect(todo.id, !!c)}
          className="mt-1"
        />
      )}

      <Checkbox
        id={`todo-${todo.id}`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
        className="mt-1"
      />

      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer block ${
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

        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {todo.tags?.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border bg-background"
              style={{ borderColor: tag.color || "currentColor" }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: tag.color || "currentColor" }}
              />
              {tag.name}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  detachTag.mutate({ todo_id: todo.id, tag_id: tag.id });
                }}
                className="hover:text-destructive ml-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {availableTags && availableTags.length > 0 && (
            <div className="relative group/tag inline-block">
              <Button
                variant="outline"
                size="icon"
                className="h-5 w-5 rounded-full border-dashed"
                title="Add tag"
              >
                <Plus className="w-3 h-3" />
              </Button>
              <select
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    attachTag.mutate({ todo_id: todo.id, tag_id: e.target.value });
                  }
                }}
              >
                <option value="" disabled>Select tag...</option>
                {availableTags.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
