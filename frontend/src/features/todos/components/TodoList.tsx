import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Tag, Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface Props { todos: Todo[]; tags: Tag[]; selected: Set<string>; onSelectionChange: (selected: Set<string>) => void; }
export function TodoList({ todos, tags, selected, onSelectionChange }: Props) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  if (!todos.length) return <div className="py-12 text-center text-muted-foreground"><p className="text-lg">No matching todos</p><p className="mt-1 text-sm">Try clearing the filters or create a todo</p></div>;
  const select = (id: string, checked: boolean) => { const next = new Set(selected); if (checked) next.add(id); else next.delete(id); onSelectionChange(next); };
  return <><div className="space-y-2">{todos.map(todo => <TodoItem key={todo.id} todo={todo} tags={tags} selected={selected.has(todo.id)} onSelect={checked => select(todo.id, checked)} onToggle={item => toggleTodo.mutate(item)} onEdit={setEditingTodo} onDelete={id => deleteTodo.mutate(id)} />)}</div>
    {editingTodo && <TodoForm mode="edit" todo={editingTodo} open onClose={() => setEditingTodo(null)} />}
  </>;
}