import { useState } from "react";
import { Plus, LogOut, CheckSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, useAttachTag, useDetachTag, type TodoFilters } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TodoFilterBar } from "./TodoFilterBar";
import { BulkActionBar } from "./BulkActionBar";
import { TagManagerDialog } from "@/features/tags/components/TagManagerDialog";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTagManager, setShowTagManager] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filters, setFilters] = useState<TodoFilters>({
    status: "all",
    keyword: "",
    tag_id: undefined,
  });

  const { data, isLoading, error } = useTodos(filters);
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const { user, logout } = useAuth();

  const handleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (!data?.items) return;
    if (selectedIds.length === data.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(data.items.map((t) => t.id));
    }
  };

  const handleAttachTag = (todoId: string, tagId: string) => {
    attachTag.mutate({ todo_id: todoId, tag_id: tagId });
  };

  const handleDetachTag = (todoId: string, tagId: string) => {
    detachTag.mutate({ todo_id: todoId, tag_id: tagId });
  };

  return (
    <div className="min-h-screen bg-muted/40 pb-20">
      {/* Header */}
      <header className="bg-card border-b">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Todo App</h1>
            {user && (
              <p className="text-sm text-muted-foreground">{user.email}</p>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <div>
              <CardTitle className="text-lg">My Todos</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Organize, filter, and tag your daily tasks
              </p>
            </div>
            <div className="flex items-center gap-2">
              {data && data.items.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                  className="text-xs"
                >
                  <CheckSquare className="h-3.5 w-3.5 mr-1" />
                  {selectedIds.length === data.items.length
                    ? "Deselect All"
                    : "Select All"}
                </Button>
              )}
              <Button size="sm" onClick={() => setShowCreateForm(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Add Todo
              </Button>
            </div>
          </CardHeader>

          <Separator />

          <CardContent className="pt-4">
            {/* Filter and Search Bar */}
            <TodoFilterBar
              filters={filters}
              onFilterChange={setFilters}
              onOpenTagManager={() => setShowTagManager(true)}
            />

            {isLoading && (
              <div className="text-center py-12 text-muted-foreground">
                Loading todos...
              </div>
            )}

            {error && (
              <div className="text-center py-12 text-destructive">
                Failed to load todos. Please try again.
              </div>
            )}

            {data && (
              <TodoList
                todos={data.items}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onAttachTag={handleAttachTag}
                onDetachTag={handleDetachTag}
              />
            )}

            {data && data.total > 0 && (
              <div className="mt-4 text-center text-sm text-muted-foreground">
                Showing {data.items.length} of {data.total} todos
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Floating Bulk Action Bar */}
      <BulkActionBar
        selectedIds={selectedIds}
        onClearSelection={() => setSelectedIds([])}
      />

      {/* Tag Manager Dialog */}
      <TagManagerDialog
        open={showTagManager}
        onClose={() => setShowTagManager(false)}
      />

      {/* Create Todo Dialog */}
      <TodoForm
        mode="create"
        open={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />
    </div>
  );
}
