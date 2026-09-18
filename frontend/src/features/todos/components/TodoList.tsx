import { useState } from "react";
import { Button } from "@/components/ui/button";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Tag, Todo } from "../api/todos";
import { useAttachTag, useBulkStatus, useDeleteTodo, useDetachTag, useToggleTodo } from "../api/todos";

export function TodoList({ todos, tags }: { todos: Todo[]; tags: Tag[] }) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null); const [selected, setSelected] = useState<string[]>([]);
  const deleteTodo = useDeleteTodo(); const toggleTodo = useToggleTodo(); const bulk = useBulkStatus(); const attach = useAttachTag(); const detach = useDetachTag();
  const select = (id: string) => setSelected((old) => old.includes(id) ? old.filter((value) => value !== id) : [...old, id]);
  if (!todos.length) return <div className="text-center py-12 text-muted-foreground"><p className="text-lg">No todos found</p><p className="text-sm mt-1">Create a todo or clear filters</p></div>;
  return <><div className="flex items-center justify-between mb-3 text-sm"><label className="flex gap-2 items-center"><input type="checkbox" checked={selected.length === todos.length} onChange={() => setSelected(selected.length === todos.length ? [] : todos.map((todo) => todo.id))} /> Select visible</label>{selected.length > 0 && <div className="flex gap-2"><Button size="sm" variant="outline" disabled={bulk.isPending} onClick={() => bulk.mutate({ todoIds: selected, completed: true })}>Mark complete</Button><Button size="sm" variant="outline" disabled={bulk.isPending} onClick={() => bulk.mutate({ todoIds: selected, completed: false })}>Mark active</Button></div>}</div><div className="space-y-2">{todos.map((todo) => <TodoItem key={todo.id} todo={todo} selected={selected.includes(todo.id)} tags={tags} onSelect={select} onToggle={(item) => toggleTodo.mutate(item)} onEdit={setEditingTodo} onDelete={(id) => deleteTodo.mutate(id)} onAttach={(todoId, tagId) => attach.mutate({ todoId, tagId })} onDetach={(todoId, tagId) => detach.mutate({ todoId, tagId })} />)}</div>{editingTodo && <TodoForm mode="edit" todo={editingTodo} open onClose={() => setEditingTodo(null)} />}</>;
}
