import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo, useBulkUpdateStatus } from "../api/todos";
import { useDetachTag } from "../../tags/api/tags";
import { BulkActions } from "./BulkActions";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkUpdateStatus = useBulkUpdateStatus();
  const detachTag = useDetachTag();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
    if (selectedIds.has(id)) {
      const newSelected = new Set(selectedIds);
      newSelected.delete(id);
      setSelectedIds(newSelected);
    }
  };

  const handleDetachTag = (todoId: string, tagId: string) => {
    detachTag.mutate({ todoId, tagId });
  };

  const toggleSelection = (id: string, selected: boolean) => {
    const newSelected = new Set(selectedIds);
    if (selected) newSelected.add(id);
    else newSelected.delete(id);
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(todos.map(t => t.id)));
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleBulkStatus = (completed: boolean) => {
    bulkUpdateStatus.mutate(
      { todo_ids: Array.from(selectedIds), completed },
      {
        onSuccess: () => setSelectedIds(new Set()),
      }
    );
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos found</p>
        <p className="text-sm mt-1">Try adjusting your filters or create a new todo</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <BulkActions
        selectedCount={selectedIds.size}
        totalCount={todos.length}
        allSelected={todos.length > 0 && selectedIds.size === todos.length}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onMarkCompleted={() => handleBulkStatus(true)}
        onMarkActive={() => handleBulkStatus(false)}
      />
      <div className="space-y-2 mt-4 flex-1">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            selected={selectedIds.has(todo.id)}
            onSelect={(selected) => toggleSelection(todo.id, selected)}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onDetachTag={(tagId) => handleDetachTag(todo.id, tagId)}
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
    </div>
  );
}
