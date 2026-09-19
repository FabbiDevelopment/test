import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import { TodoTagDialog } from "./TodoTagDialog";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
  selectedTodoIds: string[];
  onSelectionChange: (todoIds: string[]) => void;
}

export function TodoList({
  todos,
  selectedTodoIds,
  onSelectionChange,
}: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [taggingTodoId, setTaggingTodoId] = useState<string | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const taggingTodo = todos.find((todo) => todo.id === taggingTodoId) ?? null;

  const handleDelete = (todo: Todo) => {
    deleteTodo.mutate({ id: todo.id, userId: todo.user_id });
  };

  const handleSelection = (todoId: string, selected: boolean) => {
    const selectedIds = new Set(selectedTodoIds);
    if (selected) {
      selectedIds.add(todoId);
    } else {
      selectedIds.delete(todoId);
    }
    onSelectionChange([...selectedIds]);
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Create your first todo to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            selected={selectedTodoIds.includes(todo.id)}
            onSelect={handleSelection}
            onToggle={handleToggle}
            onManageTags={setTaggingTodoId}
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
      <TodoTagDialog todo={taggingTodo} onClose={() => setTaggingTodoId(null)} />
    </>
  );
}
