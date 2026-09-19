import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import { TodoTagDialog } from "./TodoTagDialog";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
  selectedIds?: Set<string>;
  onSelectToggle?: (id: string) => void;
}

export function TodoList({ todos, selectedIds, onSelectToggle }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [taggingTodo, setTaggingTodo] = useState<Todo | null>(null);
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
        <p className="text-lg">No todos match your criteria</p>
        <p className="text-sm mt-1">Try clearing filters or add a new todo</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            isSelected={selectedIds?.has(todo.id)}
            onSelectToggle={onSelectToggle}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onManageTags={(t) => setTaggingTodo(t)}
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

      {taggingTodo && (
        <TodoTagDialog
          todo={taggingTodo}
          open={!!taggingTodo}
          onClose={() => setTaggingTodo(null)}
        />
      )}
    </>
  );
}
