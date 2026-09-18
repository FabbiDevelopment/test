import { useState } from "react";
import { Button } from "@/components/ui/button";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Tag, Todo } from "../api/todos";
import {
  useAttachTag,
  useBulkStatus,
  useDeleteTodo,
  useDetachTag,
  useToggleTodo,
} from "../api/todos";

interface TodoListProps {
  todos: Todo[];
  tags: Tag[];
}

export function TodoList({ todos, tags }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkStatus = useBulkStatus();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  const updateSelection = (id: string, checked: boolean) => {
    setSelected((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const bulkUpdate = (completed: boolean) => {
    bulkStatus.mutate(
      { todoIds: [...selected], completed },
      { onSuccess: () => setSelected(new Set()) }
    );
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos found</p>
        <p className="text-sm mt-1">Create a todo or clear the current filters</p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setSelected(new Set(todos.map((todo) => todo.id)))}
        >
          Select all
        </Button>
        <Button size="sm" variant="outline" onClick={() => setSelected(new Set())}>
          Clear selection
        </Button>
        <Button size="sm" disabled={!selected.size} onClick={() => bulkUpdate(true)}>
          Mark completed
        </Button>
        <Button size="sm" disabled={!selected.size} onClick={() => bulkUpdate(false)}>
          Mark active
        </Button>
        <span className="text-xs text-muted-foreground">{selected.size} selected</span>
      </div>

      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            onToggle={(item) => toggleTodo.mutate(item)}
            onEdit={setEditingTodo}
            onDelete={(id) => deleteTodo.mutate(id)}
            selected={selected.has(todo.id)}
            onSelect={updateSelection}
            availableTags={tags}
            onAttachTag={(todoId, tagId) => attachTag.mutate({ todoId, tagId })}
            onDetachTag={(todoId, tagId) => detachTag.mutate({ todoId, tagId })}
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
