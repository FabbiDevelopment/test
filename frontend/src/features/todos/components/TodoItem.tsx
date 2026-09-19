import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon } from "lucide-react";
import type { Todo, Tag } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected?: boolean;
  onSelectToggle?: (id: string) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onManageTags?: (todo: Todo) => void;
}

export function TodoItem({
  todo,
  isSelected,
  onSelectToggle,
  onToggle,
  onEdit,
  onDelete,
  onManageTags,
}: TodoItemProps) {
  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/40 transition-colors group ${
      isSelected ? "border-primary bg-primary/5" : ""
    }`}>
      {onSelectToggle && (
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onSelectToggle(todo.id)}
          aria-label="Select todo"
        />
      )}

      <Checkbox
        id={`todo-${todo.id}`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
      />

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
          {todo.tags && todo.tags.length > 0 && (
            <div className="flex items-center gap-1">
              {todo.tags.map((tag: Tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border"
                  style={{
                    backgroundColor: tag.color ? `${tag.color}15` : "var(--muted)",
                    borderColor: tag.color || "var(--border)",
                    color: tag.color || "var(--foreground)",
                  }}
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

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {onManageTags && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            title="Manage Tags"
            onClick={() => onManageTags(todo)}
          >
            <TagIcon className="h-3.5 w-3.5" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground"
          title="Edit Todo"
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          title="Delete Todo"
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
