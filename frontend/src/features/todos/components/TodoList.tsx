import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
  selectedIds?: string[];
  onSelectToggle?: (id: string) => void;
}

export function TodoList({ todos, selectedIds = [], onSelectToggle }: TodoListProps) {
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
      <div className="text-center py-12 text-muted-foreground border rounded-lg bg-card">
        <p className="text-lg font-medium">No todos found</p>
        <p className="text-sm mt-1">Try adjusting your search filters or create a new todo</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id || index}
            todo={todo}
            index={index}
            isSelected={selectedIds.includes(todo.id)}
            onSelectToggle={onSelectToggle}
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
