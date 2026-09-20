import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";
import { useBulkStatusUpdate } from "@/features/tags/api/tags";
import { Button } from "@/components/ui/button";
import { CheckSquare, Square, CheckCircle2, XCircle } from "lucide-react";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkStatusUpdate = useBulkStatusUpdate();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
  };

  const handleSelectTodo = (id: string, selected: boolean) => {
    if (selected) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.length === todos.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(todos.map((t) => t.id));
    }
  };

  const handleBulkStatus = (completed: boolean) => {
    if (selectedIds.length === 0) return;
    bulkStatusUpdate.mutate(
      { todo_ids: selectedIds, completed },
      {
        onSuccess: () => {
          setSelectedIds([]);
        },
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

  const allSelected = todos.length > 0 && selectedIds.length === todos.length;

  return (
    <>
      {/* Bulk Action Bar */}
      <div className="flex items-center justify-between mb-3 px-1 py-1 bg-muted/30 rounded text-xs">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs flex items-center gap-1.5"
          onClick={handleSelectAll}
        >
          {allSelected ? (
            <CheckSquare className="h-3.5 w-3.5 text-primary" />
          ) : (
            <Square className="h-3.5 w-3.5 text-muted-foreground" />
          )}
          {allSelected ? "Deselect All" : "Select All"}
        </Button>

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground font-medium">
              {selectedIds.length} selected:
            </span>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs text-emerald-600 border-emerald-300"
              onClick={() => handleBulkStatus(true)}
              disabled={bulkStatusUpdate.isPending}
            >
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Mark Completed
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs text-amber-600 border-amber-300"
              onClick={() => handleBulkStatus(false)}
              disabled={bulkStatusUpdate.isPending}
            >
              <XCircle className="h-3.5 w-3.5 mr-1" /> Mark Active
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
            isSelected={selectedIds.includes(todo.id)}
            onSelect={handleSelectTodo}
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
