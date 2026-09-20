import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import { Checkbox } from "@/components/ui/checkbox";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
  selectedIds?: string[];
  onToggleSelect?: (id: string) => void;
  onSelectAll?: (selectAll: boolean) => void;
}

export function TodoList({
  todos,
  selectedIds = [],
  onToggleSelect,
  onSelectAll,
}: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos found</p>
        <p className="text-sm mt-1">Try adjusting your filters or create a new todo</p>
      </div>
    );
  }

  const allSelected = todos.length > 0 && todos.every((t) => selectedIds.includes(t.id));
  const someSelected = todos.some((t) => selectedIds.includes(t.id)) && !allSelected;

  return (
    <>
      {/* Selection header */}
      {onSelectAll && (
        <div className="flex items-center gap-2 px-3 py-1.5 mb-2 text-xs text-muted-foreground border-b pb-2">
          <Checkbox
            checked={allSelected ? true : someSelected ? "indeterminate" : false}
            onCheckedChange={(checked) => onSelectAll(Boolean(checked))}
            id="select-all-todos"
          />
          <label
            htmlFor="select-all-todos"
            className="cursor-pointer font-medium hover:text-foreground transition-colors"
          >
            {allSelected ? "Deselect all on this page" : "Select all on this page"}
          </label>
        </div>
      )}

      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            isSelected={selectedIds.includes(todo.id)}
            onToggleSelect={onToggleSelect}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>

      {editingTodo && (
        <TodoForm
          mode="edit"
          todo={editingTodo}
          open={!!editingTodo}
          onClose={() => setEditingTodo(null)}
        />
      )}
    </>
  );
}
