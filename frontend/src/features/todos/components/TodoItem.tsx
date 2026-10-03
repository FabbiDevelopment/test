import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon, X } from "lucide-react";
import type { Todo } from "../api/todos";
import { useDetachTagFromTodo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected: boolean;
  onSelect: (id: string, checked: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onAttachTag: (todo: Todo) => void;
}

export function TodoItem({ todo, isSelected, onSelect, onToggle, onEdit, onDelete, onAttachTag }: TodoItemProps) {
  const detachTag = useDetachTagFromTodo();

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      <Checkbox
        checked={isSelected}
        onCheckedChange={(checked) => onSelect(todo.id, checked as boolean)}
        className="mr-1"
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
        <div className="flex flex-wrap gap-1 mt-1">
          {todo.tags?.map(tag => (
            <span 
              key={tag.id} 
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[10px] font-medium border"
              style={{ backgroundColor: (tag.color || "#ccc") + "20", borderColor: tag.color || "#ccc", color: tag.color || "inherit" }}
            >
              {tag.name}
              <button 
                onClick={() => detachTag.mutate({ todo_id: todo.id, tag_id: tag.id })}
                className="hover:text-destructive transition-colors ml-0.5 outline-none"
              >
                <X className="h-2.5 w-2.5" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onAttachTag(todo)}
        >
          <TagIcon className="h-3.5 w-3.5" />
        </Button>
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
