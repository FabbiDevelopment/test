import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { Tag } from "../api/tags";
import {
  useAttachTag,
  useBulkStatus,
  useDeleteTodo,
  useDetachTag,
  useToggleTodo,
  type Todo,
} from "../api/todos";
import { TodoForm } from "./TodoForm";
import { TodoItem } from "./TodoItem";

interface TodoListProps {
  todos: Todo[];
  tags: Tag[];
}

export function TodoList({ todos, tags }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const bulkStatus = useBulkStatus();
  const visibleIds = new Set(todos.map((todo) => todo.id));
  const visibleSelectedIds = new Set(
    [...selectedIds].filter((id) => visibleIds.has(id)),
  );

  const setSelected = (id: string, selected: boolean) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (selected) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const runBulkUpdate = (completed: boolean) => {
    bulkStatus.mutate(
      { todoIds: [...visibleSelectedIds], completed },
      { onSuccess: () => setSelectedIds(new Set()) },
    );
  };

  if (todos.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p className="text-lg">No matching todos</p>
        <p className="mt-1 text-sm">Create a todo or clear your filters</p>
      </div>
    );
  }

  return (
    <>
      {visibleSelectedIds.size > 0 && (
        <div className="my-4 flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 p-3">
          <span className="mr-auto text-sm font-medium">
            {visibleSelectedIds.size} selected
          </span>
          <Button
            size="sm"
            onClick={() => runBulkUpdate(true)}
            disabled={bulkStatus.isPending}
          >
            Mark completed
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => runBulkUpdate(false)}
            disabled={bulkStatus.isPending}
          >
            Mark active
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelectedIds(new Set())}
          >
            Clear selection
          </Button>
        </div>
      )}

      <div className="mt-4 space-y-2">
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            availableTags={tags}
            selected={visibleSelectedIds.has(todo.id)}
            onSelectedChange={(selected) => setSelected(todo.id, selected)}
            onToggle={(item) => toggleTodo.mutate(item)}
            onEdit={setEditingTodo}
            onDelete={(id) => deleteTodo.mutate(id)}
            onAttachTag={(todoId, tagId) =>
              attachTag.mutate({ todoId, tagId })
            }
            onDetachTag={(todoId, tagId) =>
              detachTag.mutate({ todoId, tagId })
            }
          />
        ))}
      </div>

      {editingTodo && (
        <TodoForm
          mode="edit"
          todo={editingTodo}
          open
          onClose={() => setEditingTodo(null)}
        />
      )}
    </>
  );
}
