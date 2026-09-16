import { useState } from "react";
import { CheckCheck, RotateCcw, X, CheckSquare, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo, useBulkUpdateStatus } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkStatus = useBulkUpdateStatus();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
    if (selectedIds.has(id)) {
      const next = new Set(selectedIds);
      next.delete(id);
      setSelectedIds(next);
    }
  };

  const handleSelectChange = (id: string, selected: boolean) => {
    const next = new Set(selectedIds);
    if (selected) {
      next.add(id);
    } else {
      next.delete(id);
    }
    setSelectedIds(next);
  };

  const handleSelectAll = () => {
    if (selectedIds.size === todos.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(todos.map((t) => t.id)));
    }
  };

  const handleBulkComplete = (completed: boolean) => {
    if (selectedIds.size === 0) return;
    bulkStatus.mutate(
      {
        todo_ids: Array.from(selectedIds),
        completed,
      },
      {
        onSuccess: () => {
          setSelectedIds(new Set());
        },
      }
    );
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos match your criteria</p>
        <p className="text-sm mt-1">Create a new todo or adjust your filters</p>
      </div>
    );
  }

  const allSelected = todos.length > 0 && selectedIds.size === todos.length;

  return (
    <>
      {/* Bulk action toolbar */}
      <div className="flex items-center justify-between p-2.5 mb-3 rounded-lg border bg-muted/30 text-xs">
        <button
          type="button"
          onClick={handleSelectAll}
          className="flex items-center gap-1.5 font-medium hover:text-foreground text-muted-foreground transition-colors"
        >
          {allSelected ? (
            <CheckSquare className="h-4 w-4 text-primary" />
          ) : (
            <Square className="h-4 w-4" />
          )}
          <span>
            {allSelected ? "Deselect All" : "Select All"} ({selectedIds.size}/{todos.length})
          </span>
        </button>

        {selectedIds.size > 0 && (
          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              onClick={() => handleBulkComplete(true)}
              disabled={bulkStatus.isPending}
            >
              <CheckCheck className="h-3.5 w-3.5 mr-1 text-emerald-600" />
              Mark Complete
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              onClick={() => handleBulkComplete(false)}
              disabled={bulkStatus.isPending}
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1 text-amber-600" />
              Mark Active
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground"
              onClick={() => setSelectedIds(new Set())}
              title="Clear selection"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            isSelected={selectedIds.has(todo.id)}
            onSelectChange={(selected) => handleSelectChange(todo.id, selected)}
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
