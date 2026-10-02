import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { Tag, Todo } from "../api/todos";
import {
  useAttachTag,
  useBulkUpdateTodoStatus,
  useDeleteTodo,
  useDetachTag,
  useToggleTodo,
} from "../api/todos";
import { TodoForm } from "./TodoForm";
import { TodoItem } from "./TodoItem";

interface TodoListProps {
  todos: Todo[];
  tags: Tag[];
  hasActiveFilters: boolean;
}

export function TodoList({ todos, tags, hasActiveFilters }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkUpdate = useBulkUpdateTodoStatus();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const selectedTodos = todos.filter((todo) => selectedIds.has(todo.id));

  const handleSelect = (todoId: string, selected: boolean) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (selected) next.add(todoId);
      else next.delete(todoId);
      return next;
    });
  };

  const selectAll = () => setSelectedIds(new Set(todos.map((todo) => todo.id)));

  const updateSelectedStatus = (completed: boolean) => {
    bulkUpdate.mutate(
      { todo_ids: selectedTodos.map((todo) => todo.id), completed },
      { onSuccess: () => setSelectedIds(new Set()) }
    );
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">
          {hasActiveFilters ? "No todos match these filters" : "No todos yet"}
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3">
        <div className="flex items-center gap-2 text-sm">
          <Checkbox
            aria-label="Select all visible todos"
            checked={selectedTodos.length === todos.length}
            onCheckedChange={(checked) =>
              checked === true ? selectAll() : setSelectedIds(new Set())
            }
          />
          <span>{selectedTodos.length} selected</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!selectedTodos.length || bulkUpdate.isPending}
            onClick={() => updateSelectedStatus(true)}
          >
            Mark completed
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!selectedTodos.length || bulkUpdate.isPending}
            onClick={() => updateSelectedStatus(false)}
          >
            Mark active
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            tags={tags}
            selected={selectedIds.has(todo.id)}
            onSelect={handleSelect}
            onToggle={(item) => toggleTodo.mutate(item)}
            onEdit={setEditingTodo}
            onDelete={(id) => {
              setSelectedIds((previous) => {
                const next = new Set(previous);
                next.delete(id);
                return next;
              });
              deleteTodo.mutate(id);
            }}
            onAttachTag={(todoId, tagId) => attachTag.mutate({ todoId, tagId })}
            onDetachTag={(todoId, tagId) => detachTag.mutate({ todoId, tagId })}
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
