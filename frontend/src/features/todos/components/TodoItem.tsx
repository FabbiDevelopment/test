import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon, Plus } from "lucide-react";
import type { Todo } from "../api/todos";
import { TagBadge } from "@/features/tags/components/TagBadge";
import { useTags, useAttachTagToTodo, useDetachTagFromTodo } from "@/features/tags/api/tags";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected: boolean;
  onSelectChange: (selected: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({
  todo,
  isSelected,
  onSelectChange,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const { data: allTags = [] } = useTags();
  const attachTag = useAttachTagToTodo();
  const detachTag = useDetachTagFromTodo();
  const [showTagMenu, setShowTagMenu] = useState(false);

  const attachedTagIds = new Set((todo.tags || []).map((t) => t.id));
  const availableTags = allTags.filter((t) => !attachedTagIds.has(t.id));

  const handleDetachTag = (tagId: string) => {
    detachTag.mutate({ todoId: todo.id, tagId });
  };

  const handleAttachTag = (tagId: string) => {
    attachTag.mutate({ todoId: todo.id, tagId });
    setShowTagMenu(false);
  };

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border transition-colors group ${
        isSelected
          ? "bg-accent/70 border-primary/40"
          : "bg-card hover:bg-accent/40"
      }`}
    >
      {/* Bulk selection checkbox */}
      <div className="pt-0.5">
        <Checkbox
          id={`select-${todo.id}`}
          checked={isSelected}
          onCheckedChange={(checked) => onSelectChange(Boolean(checked))}
          title="Select for bulk action"
        />
      </div>

      {/* Completion toggle checkbox */}
      <div className="pt-0.5">
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
          className="rounded-full data-[state=checked]:bg-emerald-600 data-[state=checked]:border-emerald-600"
          title={todo.completed ? "Mark incomplete" : "Mark complete"}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer block leading-tight ${
            todo.completed ? "line-through text-muted-foreground" : ""
          }`}
        >
          {todo.title}
        </label>
        {todo.description && (
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {todo.description}
          </p>
        )}

        {/* Attached tags list */}
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {(todo.tags || []).map((tag) => (
            <TagBadge
              key={tag.id}
              tag={tag}
              onRemove={() => handleDetachTag(tag.id)}
            />
          ))}

          {/* Quick attach tag button */}
          <div className="relative inline-block">
            <button
              type="button"
              onClick={() => setShowTagMenu(!showTagMenu)}
              className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground border border-dashed rounded-full px-1.5 py-0.5 hover:bg-accent/50 transition-colors"
              title="Attach tag"
            >
              <Plus className="h-2.5 w-2.5" />
              <TagIcon className="h-2.5 w-2.5" />
            </button>

            {showTagMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowTagMenu(false)}
                />
                <div className="absolute left-0 mt-1 w-44 rounded-md border bg-popover text-popover-foreground shadow-md p-1.5 z-50 text-xs">
                  <div className="font-semibold px-1 py-0.5 text-[10px] text-muted-foreground uppercase">
                    Attach Tag
                  </div>
                  {availableTags.length === 0 ? (
                    <div className="px-1 py-1 text-muted-foreground text-[11px]">
                      {allTags.length === 0 ? "No tags created yet" : "All tags attached"}
                    </div>
                  ) : (
                    availableTags.map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => handleAttachTag(t.id)}
                        className="w-full flex items-center gap-2 px-1.5 py-1 rounded hover:bg-accent text-left"
                      >
                        <span
                          className="h-2 w-2 rounded-full shrink-0"
                          style={{ backgroundColor: t.color || "#3B82F6" }}
                        />
                        <span className="truncate">{t.name}</span>
                      </button>
                    ))
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Action buttons */}
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
