import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import { BulkActionBar } from "./BulkActionBar";
import { Checkbox } from "@/components/ui/checkbox";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";

interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  const handleSelectChange = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    }
  };

  const isAllSelected = todos.length > 0 && selectedIds.length === todos.length;

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(todos.map((t) => t.id));
    } else {
      setSelectedIds([]);
    }
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-base font-medium">Không tìm thấy công việc nào</p>
        <p className="text-xs mt-1">Hãy thử thay đổi bộ lọc hoặc tạo công việc mới</p>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between pb-2 px-1 text-xs text-muted-foreground border-b mb-3">
        <div className="flex items-center gap-2">
          <Checkbox
            checked={isAllSelected}
            onCheckedChange={(checked) => handleSelectAll(!!checked)}
            id="select-all"
          />
          <label htmlFor="select-all" className="cursor-pointer font-medium hover:text-foreground">
            {isAllSelected ? "Bỏ chọn tất cả" : "Chọn tất cả trang này"}
          </label>
        </div>

        <span>
          Đã chọn {selectedIds.length} / {todos.length}
        </span>
      </div>

      <div className="space-y-2.5">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            isSelected={selectedIds.includes(todo.id)}
            onSelectChange={handleSelectChange}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>


      <BulkActionBar
        selectedIds={selectedIds}
        onClearSelection={() => setSelectedIds([])}
      />

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
