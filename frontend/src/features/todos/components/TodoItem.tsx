import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";
import type { Todo } from "../api/todos";
import { TagBadge } from "../../tags/components/TagBadge";

interface TodoItemProps {
  todo: Todo;
  index: number;
  selected?: boolean;
  onSelect?: (selected: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onDetachTag?: (tagId: string) => void;
}

export function TodoItem({ todo, selected, onSelect, onToggle, onEdit, onDelete, onDetachTag }: TodoItemProps) {
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border bg-card transition-colors group ${selected ? 'ring-1 ring-primary' : 'hover:bg-accent/50'}`}>
      <div className="flex flex-col gap-2 mt-0.5">
        <Checkbox
          checked={selected}
          onCheckedChange={(c) => onSelect?.(c === true)}
          className="data-[state=checked]:bg-primary rounded-[4px]"
        />
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
          className="rounded-full"
        />
      </div>

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
        {todo.tags && todo.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {todo.tags.map((tag) => (
              <TagBadge
                key={tag.id}
                tag={tag}
                onRemove={onDetachTag ? () => onDetachTag(tag.id) : undefined}
              />
            ))}
          </div>
        )}
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
