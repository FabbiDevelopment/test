import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useBulkUpdateStatus, useDeleteTodo, useToggleTodo } from "../api/todos";
import { Button } from "@/components/ui/button";
import type { Tag } from "@/features/tags/api/tags";

interface TodoListProps {
  todos: Todo[];
  tags: Tag[];
  selectedIds: string[];
  onSelectChange: (ids: string[]) => void;
}

export function TodoList({
  todos,
  tags,
  selectedIds,
  onSelectChange,
}: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkUpdate = useBulkUpdateStatus();

  const toggleSelect = (id: string) => {
    onSelectChange(
      selectedIds.includes(id)
        ? selectedIds.filter((x) => x !== id)
        : [...selectedIds, id]
    );
  };

  const handleBulk = (completed: boolean) => {
    if (selectedIds.length === 0) return;
    bulkUpdate.mutate(
      { todoIds: selectedIds, completed },
      { onSuccess: () => onSelectChange([]) }
    );
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Create your first todo or adjust filters</p>
      </div>
    );
  }

  return (
    <>
      {/* THÊM: bulk actions — Level 4 */}
      {selectedIds.length > 0 && (
        <div className="flex gap-2 mb-3">
          <Button size="sm" variant="outline" onClick={() => handleBulk(true)}>
            Mark completed ({selectedIds.length})
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleBulk(false)}>
            Mark active ({selectedIds.length})
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {todos.map((todo) => (
          <TodoItem
            // SAI: key={index} — React reconcile sai khi xóa/sắp xếp
            // THÊM: key={todo.id} stable identity
            key={todo.id}
            todo={todo}
            tags={tags}
            selected={selectedIds.includes(todo.id)}
            onSelect={() => toggleSelect(todo.id)}
            onToggle={(t) => toggleTodo.mutate(t)}
            onEdit={setEditingTodo}
            onDelete={(id) => deleteTodo.mutate(id)}
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
