import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Pencil, Trash2 } from "lucide-react";
import { TagPicker } from "@/features/tags/components/TagPicker";
import type { Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  selected: boolean;
  onSelectChange: (id: string, selected: boolean) => void;
}

export function TodoItem({
  todo,
  onToggle,
  onEdit,
  onDelete,
  selected,
  onSelectChange,
}: TodoItemProps) {
  return (
    <div
      className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group"
      data-testid="todo-item"
    >
      <Checkbox
        aria-label={`Select ${todo.title}`}
        checked={selected}
        onCheckedChange={(checked) => onSelectChange(todo.id, checked === true)}
        className="mt-1"
      />

      <Checkbox
        id={`todo-${todo.id}`}
        aria-label={`Mark ${todo.title} as complete`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
        className="mt-1"
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
        {todo.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {todo.tags.map((tag) => (
              <Badge
                key={tag.id}
                style={{
                  borderColor: tag.color ?? undefined,
                  color: tag.color ?? undefined,
                }}
              >
                {tag.name}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <TagPicker todoId={todo.id} attachedTags={todo.tags} />
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
