import { useState } from "react";
import { Plus, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, type TodoFilterParams } from "../api/todos";
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
  const [filters, setFilters] = useState<TodoFilterParams>({
    page: 1,
    size: 20,
  });

  const { data, isLoading, error } = useTodos(filters);
  const { user, logout } = useAuth();

  const handleFilterChange = (newFilters: Partial<TodoFilterParams>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setSelectedIds([]); // Clear selection on filter change
  };

  const handleResetFilters = () => {
    setFilters({ page: 1, size: 20 });
    setSelectedIds([]);
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAll = (selectAll: boolean) => {
    if (!data?.items) return;
    if (selectAll) {
      const allPageIds = data.items.map((t) => t.id);
      setSelectedIds(Array.from(new Set([...selectedIds, ...allPageIds])));
    } else {
      const pageIds = new Set(data.items.map((t) => t.id));
      setSelectedIds((prev) => prev.filter((id) => !pageIds.has(id)));
    }
  };

  return (
    <div className="min-h-screen bg-muted/40">
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
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">My Todos</CardTitle>
            <Button size="sm" onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Add Todo
            </Button>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
            {/* Filter and Search Bar */}
            <TodoFilterBar
              filters={filters}
              onFilterChange={handleFilterChange}
              onResetFilters={handleResetFilters}
              onOpenTagManager={() => setShowTagManager(true)}
            />

            {/* Bulk Action Toolbar */}
            <BulkActionBar
              selectedIds={selectedIds}
              onClearSelection={() => setSelectedIds([])}
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
                onToggleSelect={handleToggleSelect}
                onSelectAll={handleSelectAll}
              />
            )}

            {data && data.total > 0 && (
              <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Showing {data.items.length} of {data.total} todos
                </span>
                {data.total > (filters.size || 20) && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(filters.page || 1) <= 1}
                      onClick={() =>
                        handleFilterChange({ page: (filters.page || 1) - 1 })
                      }
                      className="h-7 px-2 text-xs"
                    >
                      Previous
                    </Button>
                    <span>Page {filters.page || 1}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={
                        (filters.page || 1) * (filters.size || 20) >= data.total
                      }
                      onClick={() =>
                        handleFilterChange({ page: (filters.page || 1) + 1 })
                      }
                      className="h-7 px-2 text-xs"
                    >
                      Next
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Create Todo Dialog */}
      <TodoForm
        mode="create"
        open={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />

      {/* Tag Manager Dialog */}
      <TagManagerDialog
        open={showTagManager}
        onClose={() => setShowTagManager(false)}
      />
    </div>
  );
}
