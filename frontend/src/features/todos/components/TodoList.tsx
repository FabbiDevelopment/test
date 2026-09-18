import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useUpdateTodo } from "../api/todos";

export function TodoList({ todos, selectedIds, onSelectChange, onDelete, busy }: {
  todos: Todo[]; selectedIds: Set<string>; onSelectChange: (id: string, checked: boolean) => void;
  onDelete: () => void; busy: boolean;
}) {
  const [editing, setEditing] = useState<Todo | null>(null);
  const remove = useDeleteTodo(), update = useUpdateTodo();
  return <>
    {todos.length === 0 && <p className="py-8 text-center" role="status">No todos match your filters.</p>}
    <div className="space-y-2">
      {todos.map((todo) => <TodoItem key={todo.id} todo={todo} selected={selectedIds.has(todo.id)}
        pending={busy || remove.isPending || update.isPending}
        onSelectChange={(checked) => onSelectChange(todo.id, checked)}
        onToggle={() => update.mutate({ id: todo.id, data: { completed: !todo.completed } })}
        onEdit={() => setEditing(todo)} onDelete={() => remove.mutate(todo.id, { onSuccess: onDelete })} />)}
    </div>
    {editing && <TodoForm mode="edit" todo={editing} open onClose={() => setEditing(null)} />}
  </>;
}
