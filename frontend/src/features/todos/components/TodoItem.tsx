import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon } from "lucide-react";
import type { Todo } from "../api/todos";
import { useTags, useAttachTag, useDetachTag } from "@/features/tags/api/tags";

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
  isSelected = false,
  onSelect,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const { data: allTags = [] } = useTags();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const [showTagDropdown, setShowTagDropdown] = useState(false);

  const attachedTagIds = new Set((todo.tags || []).map((t) => t.id));

  const handleToggleTag = (tagId: string) => {
    if (attachedTagIds.has(tagId)) {
      detachTag.mutate({ todoId: todo.id, tagId });
    } else {
      attachTag.mutate({ todoId: todo.id, tagId });
    }
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group relative">
      {/* Bulk selection checkbox */}
      {onSelect && (
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelect(todo.id, !!checked)}
          title="Select for bulk action"
        />
      )}

      {/* Completion checkbox */}
      <Checkbox
        id={`todo-${todo.id}`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
      />

      {/* Main info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <label
            htmlFor={`todo-${todo.id}`}
            className={`text-sm font-medium cursor-pointer ${
              todo.completed ? "line-through text-muted-foreground" : ""
            }`}
          >
            {todo.title}
          </label>

          {/* Attached Tag Badges */}
          {todo.tags && todo.tags.length > 0 && (
            <div className="flex items-center gap-1">
              {todo.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium text-white"
                  style={{ backgroundColor: tag.color || "#6b7280" }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {todo.description && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            {todo.description}
          </p>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {/* Attach Tag Menu Trigger */}
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground"
            onClick={() => setShowTagDropdown(!showTagDropdown)}
            title="Attach/Detach Tag"
          >
            <TagIcon className="h-3.5 w-3.5" />
          </Button>

          {showTagDropdown && (
            <div className="absolute right-0 top-9 z-20 w-44 rounded-md border bg-popover p-2 shadow-md text-xs space-y-1">
              <p className="font-semibold text-muted-foreground px-1 mb-1">Toggle Tags:</p>
              {allTags.length === 0 ? (
                <p className="text-muted-foreground px-1 py-1">No tags available.</p>
              ) : (
                allTags.map((tag) => (
                  <button
                    key={tag.id}
                    type="button"
                    className={`w-full flex items-center justify-between px-2 py-1 rounded text-left hover:bg-accent ${
                      attachedTagIds.has(tag.id) ? "font-bold bg-accent/50" : ""
                    }`}
                    onClick={() => handleToggleTag(tag.id)}
                  >
                    <span className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: tag.color || "#6b7280" }} />
                      {tag.name}
                    </span>
                    {attachedTagIds.has(tag.id) && "✓"}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

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
