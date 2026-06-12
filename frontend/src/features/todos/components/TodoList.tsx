import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo, useBulkUpdateStatus } from "../api/todos";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkUpdate = useBulkUpdateStatus();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
  };

  const handleSelect = (id: string, selected: boolean) => {
    const newSet = new Set(selectedIds);
    if (selected) newSet.add(id);
    else newSet.delete(id);
    setSelectedIds(newSet);
  };

  const handleSelectAll = (checked: boolean | "indeterminate") => {
    if (checked === true) {
      setSelectedIds(new Set(todos.map(t => t.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleBulkUpdate = (completed: boolean) => {
    bulkUpdate.mutate({ todo_ids: Array.from(selectedIds), completed }, {
      onSuccess: () => setSelectedIds(new Set())
    });
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Create your first todo to get started</p>
      </div>
    );
  }

  const allSelected = todos.length > 0 && selectedIds.size === todos.length;

  return (
    <>
      {todos.length > 0 && (
        <div className="flex items-center gap-4 mb-4 p-2 bg-muted/30 rounded-md">
          <div className="flex items-center gap-2">
            <Checkbox 
              checked={allSelected} 
              onCheckedChange={handleSelectAll} 
              id="select-all"
            />
            <label htmlFor="select-all" className="text-sm font-medium cursor-pointer">
              Select All
            </label>
          </div>
          
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-sm text-muted-foreground mr-2">
                {selectedIds.size} selected
              </span>
              <Button size="sm" variant="outline" onClick={() => handleBulkUpdate(true)}>
                Mark Completed
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleBulkUpdate(false)}>
                Mark Active
              </Button>
            </div>
          )}
        </div>
      )}

      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
            selected={selectedIds.has(todo.id)}
            onSelect={handleSelect}
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
