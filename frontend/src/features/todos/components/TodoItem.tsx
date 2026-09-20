import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon, Plus } from "lucide-react";
import type { Todo } from "../api/todos";
import { useAttachTag, useDetachTag } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";
import { TagBadge } from "@/features/tags/components/TagBadge";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected?: boolean;
  onToggleSelect?: (id: string) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({
  todo,
  isSelected = false,
  onToggleSelect,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const { data: allTagsData } = useTags();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const [showTagPicker, setShowTagPicker] = useState(false);

  const attachedTagIds = new Set((todo.tags || []).map((t) => t.id));
  const availableTags = (allTagsData?.items || []).filter(
    (t) => !attachedTagIds.has(t.id)
  );

  const handleDetachTag = (tagId: string) => {
    detachTag.mutate({ todoId: todo.id, tagId });
  };

  const handleAttachTag = (tagId: string) => {
    attachTag.mutate(
      { todoId: todo.id, tagId },
      {
        onSuccess: () => setShowTagPicker(false),
      }
    );
  };

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border bg-card transition-colors group relative ${
        isSelected ? "border-primary/50 bg-primary/5" : "hover:bg-accent/40"
      }`}
    >
      {/* Bulk selection checkbox */}
      {onToggleSelect && (
        <div className="pt-0.5" title="Select for bulk action">
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelect(todo.id)}
            className="border-muted-foreground/40 data-[state=checked]:border-primary"
          />
        </div>
      )}

      {/* Completion toggle checkbox */}
      <div className="pt-0.5">
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
        />
      </div>

      {/* Title, description, and tags */}
      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer block leading-snug ${
            todo.completed ? "line-through text-muted-foreground" : ""
          }`}
        >
          {todo.title}
        </label>

        {todo.description && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
            {todo.description}
          </p>
        )}

        {/* Attached tags list */}
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {todo.tags &&
            todo.tags.map((tag) => (
              <TagBadge
                key={tag.id}
                tag={tag}
                size="sm"
                onRemove={() => handleDetachTag(tag.id)}
              />
            ))}

          {/* Quick attach tag button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowTagPicker(!showTagPicker)}
              className="inline-flex items-center gap-0.5 text-xs text-muted-foreground hover:text-foreground px-1.5 py-0.5 rounded border border-dashed hover:border-foreground/40 transition-colors"
              title="Add tag"
            >
              <Plus className="h-2.5 w-2.5" />
              <TagIcon className="h-2.5 w-2.5 mr-0.5" />
              <span>Tag</span>
            </button>

            {/* Tag picker dropdown */}
            {showTagPicker && (
              <div className="absolute left-0 top-full mt-1 z-30 min-w-[140px] max-w-[200px] p-1.5 bg-popover text-popover-foreground rounded-md border shadow-md animate-in fade-in-50">
                <p className="text-[10px] font-semibold text-muted-foreground px-1 mb-1">
                  Select Tag
                </p>
                {availableTags.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic px-1 py-1">
                    No more tags
                  </p>
                ) : (
                  <div className="space-y-1 max-h-36 overflow-y-auto">
                    {availableTags.map((tag) => (
                      <button
                        key={tag.id}
                        type="button"
                        onClick={() => handleAttachTag(tag.id)}
                        className="w-full flex items-center gap-1.5 px-1.5 py-1 text-xs rounded hover:bg-muted text-left transition-colors"
                      >
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: tag.color || "#3b82f6" }}
                        />
                        <span className="truncate">{tag.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Action buttons (edit, delete) */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onEdit(todo)}
          title="Edit todo"
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          onClick={() => onDelete(todo.id)}
          title="Delete todo"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
