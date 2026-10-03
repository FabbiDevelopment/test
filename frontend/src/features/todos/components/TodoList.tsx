import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";
import { TagAttachModal } from "./TagAttachModal";
import { BulkActionsToolbar } from "./BulkActionsToolbar";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [tagAttachTodo, setTagAttachTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleSelect = (id: string, checked: boolean) => {
    setSelectedIds(prev => checked ? [...prev, id] : prev.filter(item => item !== id));
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? todos.map(t => t.id) : []);
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos found</p>
      </div>
    );
  }

  return (
    <>
      <BulkActionsToolbar 
        selectedIds={selectedIds}
        allIds={todos.map(t => t.id)}
        onClearSelection={() => setSelectedIds([])}
        onSelectAll={handleSelectAll}
      />
      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={index}
            todo={todo}
            index={index}
            isSelected={selectedIds.includes(todo.id)}
            onSelect={handleSelect}
            onToggle={handleToggle}
            onEdit={setEditingTodo}
            onDelete={(id) => deleteTodo.mutate(id)}
            onAttachTag={setTagAttachTodo}
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

      {tagAttachTodo && (
        <TagAttachModal 
          todo={tagAttachTodo}
          onClose={() => setTagAttachTodo(null)}
        />
      )}
    </>
  );
}
