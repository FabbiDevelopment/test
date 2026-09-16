import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";
import type { Todo } from "../api/todos";
import type { Tag } from "@/features/tags/api/tags";
import { useAttachTag } from "@/features/tags/api/tags";

interface TodoItemProps {
  todo: Todo;
  tags: Tag[];
  selected: boolean;
  onSelect: () => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({
  todo,
  tags,
  selected,
  onSelect,
  onToggle,
  onEdit,
  onDelete,
}: TodoItemProps) {
  const attachTag = useAttachTag();

  const handleAttachTag = () => {
    if (tags.length === 0) return;
    const tagId = window.prompt(
      `Attach tag ID:\n${tags.map((t) => `${t.name}: ${t.id}`).join("\n")}`
    );
    if (!tagId) return;
    attachTag.mutate({ todoId: todo.id, tagId });
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      {/* THÊM: bulk selection checkbox */}
      <Checkbox checked={selected} onCheckedChange={onSelect} aria-label="Select todo" />

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
        {/* THÊM: hiển thị tags đính kèm — Level 4 */}
        {todo.tags && todo.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {todo.tags.map((tag) => (
              <span
                key={tag.id}
                className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary"
                style={{ color: tag.color ?? undefined }}
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button variant="ghost" size="sm" onClick={handleAttachTag}>
          Tag
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(todo)}>
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
