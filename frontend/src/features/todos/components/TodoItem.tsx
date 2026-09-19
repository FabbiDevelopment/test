import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Plus, X } from "lucide-react";
import type { Todo } from "../api/todos";
import { useTags } from "@/features/tags/api/tagsApi";
import { useAttachTag, useDetachTag } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected: boolean;
  onSelectChange: (todoId: string, checked: boolean) => void;
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
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const [showTagMenu, setShowTagMenu] = useState(false);

  const attachedTags = todo.tags || [];
  const availableTags = allTags.filter(
    (tag) => !attachedTags.some((t) => t.id === tag.id)
  );

  const handleAttachTag = (tagId: string) => {
    attachTag.mutate({ todoId: todo.id, tagId });
    setShowTagMenu(false);
  };

  const handleDetachTag = (tagId: string) => {
    detachTag.mutate({ todoId: todo.id, tagId });
  };

  return (
    <div
      className={`flex items-start gap-3 p-3.5 rounded-xl border transition-all group ${isSelected
          ? "bg-primary/5 border-primary/40 shadow-sm"
          : "bg-card hover:bg-accent/40"
        }`}
    >
      <div className="pt-0.5">
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelectChange(todo.id, !!checked)}
          aria-label="Chọn công việc"
        />
      </div>

      <div className="pt-0.5">
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
          className="rounded-full data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500"
        />
      </div>

      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-semibold cursor-pointer block leading-tight ${todo.completed ? "line-through text-muted-foreground/70" : "text-foreground"
            }`}
        >
          {todo.title}
        </label>

        {todo.description && (
          <p className="text-xs text-muted-foreground mt-1 whitespace-pre-line leading-relaxed">
            {todo.description}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {attachedTags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium border shadow-2xs group/tag"
              style={{
                backgroundColor: `${tag.color || "#3B82F6"}15`,
                color: tag.color || "#3B82F6",
                borderColor: `${tag.color || "#3B82F6"}40`,
              }}
            >
              <span>🏷️ {tag.name}</span>
              <button
                type="button"
                onClick={() => handleDetachTag(tag.id)}
                className="opacity-60 hover:opacity-100 hover:text-destructive transition-opacity"
              >
                <X className="h-2.5 w-2.5" />
              </button>
            </span>
          ))}

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowTagMenu(!showTagMenu)}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] text-muted-foreground hover:text-foreground border border-dashed border-muted-foreground/40 hover:border-foreground/60 transition-colors"
            >
              <Plus className="h-2.5 w-2.5" />
              <span>Thêm thẻ</span>
            </button>

            {showTagMenu && (
              <div className="absolute left-0 top-full mt-1 z-20 min-w-36 bg-popover text-popover-foreground rounded-lg shadow-lg border p-1 text-xs animate-in fade-in zoom-in-95">
                {availableTags.length === 0 ? (
                  <p className="p-2 text-[11px] text-muted-foreground text-center">
                    {allTags.length === 0 ? "Chưa có thẻ nào" : "Đã gắn hết thẻ"}
                  </p>
                ) : (
                  availableTags.map((tag) => (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => handleAttachTag(tag.id)}
                      className="w-full text-left px-2 py-1.5 rounded hover:bg-accent flex items-center gap-2 text-xs"
                    >
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: tag.color || "#3B82F6" }}
                      />
                      <span>{tag.name}</span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-destructive hover:text-destructive"
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
