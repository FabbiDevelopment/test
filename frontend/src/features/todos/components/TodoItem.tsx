import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";
import type { Tag, Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  selected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  availableTags: Tag[];
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoItem({ todo, onToggle, onEdit, onDelete, selected, onSelect, availableTags, onAttachTag, onDetachTag }: TodoItemProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      <Checkbox
        aria-label={`Select ${todo.title}`}
        checked={selected}
        onCheckedChange={(checked) => onSelect(todo.id, checked === true)}
      />
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
        <div className="mt-1 flex flex-wrap items-center gap-1">
          {todo.tags.map((tag) => (
            <button
              type="button"
              key={tag.id}
              onClick={() => onDetachTag(todo.id, tag.id)}
              className="rounded-full border px-2 py-0.5 text-xs"
              style={{ color: tag.color || undefined }}
              aria-label={`Remove tag ${tag.name} from ${todo.title}`}
            >
              {tag.name} ×
            </button>
          ))}
          <select
            aria-label={`Attach tag to ${todo.title}`}
            className="rounded border bg-transparent text-xs"
            value=""
            onChange={(event) => event.target.value && onAttachTag(todo.id, event.target.value)}
          >
            <option value="">+ tag</option>
            {availableTags.filter((tag) => !todo.tags.some((item) => item.id === tag.id)).map((tag) => (
              <option key={tag.id} value={tag.id}>{tag.name}</option>
            ))}
          </select>
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
