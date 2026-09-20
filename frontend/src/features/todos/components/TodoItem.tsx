import React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, X } from "lucide-react";
import type { Todo } from "../api/todos";
import { useTags, useAttachTag, useDetachTag, type Tag } from "../api/tags";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected?: boolean;
  onSelectToggle?: (id: string) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({
  todo,
  isSelected = false,
  onSelectToggle,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const { data: userTags = [] } = useTags();
  const attachTagMutation = useAttachTag();
  const detachTagMutation = useDetachTag();

  const handleAttachTag = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const tagId = e.target.value;
    if (!tagId) return;
    attachTagMutation.mutate({ todoId: todo.id, tagId });
    e.target.value = "";
  };

  const handleDetachTag = (tagId: string) => {
    detachTagMutation.mutate({ todoId: todo.id, tagId });
  };

  // Filter available tags that are not yet attached
  const unattachedTags = userTags.filter(
    (ut: Tag) => !todo.tags?.some((t) => t.id === ut.id)
  );

  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-lg border transition-colors group ${
        isSelected ? "bg-accent/80 border-primary" : "bg-card hover:bg-accent/40"
      }`}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {/* Selection checkbox for bulk actions */}
        {onSelectToggle && (
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onSelectToggle(todo.id)}
            aria-label={`Select ${todo.title}`}
          />
        )}

        {/* Completion status checkbox */}
        <Checkbox
          id={`todo-${todo.id}`}
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

          {/* Attached Tag Badges */}
          {todo.tags && todo.tags.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {todo.tags.map((t) => (
                <span
                  key={t.id}
                  style={{
                    backgroundColor: `${t.color || "#3b82f6"}20`,
                    borderColor: t.color || "#3b82f6",
                    color: t.color || "#3b82f6",
                  }}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium border"
                >
                  🏷️ {t.name}
                  <button
                    onClick={() => handleDetachTag(t.id)}
                    className="hover:opacity-80 rounded-full p-0.5"
                  >
                    <X className="h-2.5 w-2.5" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons & Tag Attachment */}
      <div className="flex items-center gap-2 self-end sm:self-center">
        {/* Attach Tag Select */}
        {unattachedTags.length > 0 && (
          <select
            defaultValue=""
            onChange={handleAttachTag}
            className="h-7 text-xs px-2 rounded border bg-background text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="" disabled>
              + Tag
            </option>
            {unattachedTags.map((ut: Tag) => (
              <option key={ut.id} value={ut.id}>
                {ut.name}
              </option>
            ))}
          </select>
        )}

        <div className="flex items-center gap-1 opacity-90 sm:opacity-0 group-hover:opacity-100 transition-opacity">
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
    </div>
  );
}
