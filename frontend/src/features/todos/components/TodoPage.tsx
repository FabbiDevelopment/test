import { useState } from "react";
import { Plus, LogOut, Tags, CheckSquare, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, useBulkUpdateTodos, type TodoFilters } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TodoFilterBar } from "./TodoFilterBar";
import { TagManager } from "@/features/tags/components/TagManager";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Checkbox } from "@/components/ui/checkbox";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTagManager, setShowTagManager] = useState(false);
  const [filters, setFilters] = useState<TodoFilters>({});
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  const { data, isLoading, error } = useTodos(filters);
  const bulkUpdate = useBulkUpdateTodos();
  const { user, logout } = useAuth();

  const handleSelect = (id: string, selected: boolean) => {
    setSelectedIds((prev) =>
      selected ? [...prev, id] : prev.filter((i) => i !== id)
    );
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected && data) {
      setSelectedIds(data.items.map((t) => t.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleBulkUpdate = (completed: boolean) => {
    if (selectedIds.length === 0) return;
    bulkUpdate.mutate(
      { todo_ids: selectedIds, completed },
      {
        onSuccess: () => setSelectedIds([]),
      }
    );
  };

  const allSelected =
    data?.items.length! > 0 && selectedIds.length === data?.items.length;

  return (
    <div className="min-h-screen bg-muted/40">
      {/* Header */}
      <header className="bg-card border-b">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
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
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-2xl font-semibold tracking-tight">My Todos</h2>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setShowTagManager(true)}>
                <Tags className="h-4 w-4 mr-2" />
                Manage Tags
              </Button>
              <Button onClick={() => setShowCreateForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Todo
              </Button>
            </div>
          </div>
          <TodoFilterBar filters={filters} onChange={setFilters} />
        </div>

        <Card>
          <CardHeader className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={(c) => handleSelectAll(!!c)}
                    id="select-all"
                  />
                  <label htmlFor="select-all" className="text-sm font-medium cursor-pointer">
                    Select All
                  </label>
                </div>
                {selectedIds.length > 0 && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">
                      ({selectedIds.length} selected)
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7"
                      onClick={() => handleBulkUpdate(true)}
                    >
                      <CheckSquare className="h-3.5 w-3.5 mr-1" /> Mark Done
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7"
                      onClick={() => handleBulkUpdate(false)}
                    >
                      <Square className="h-3.5 w-3.5 mr-1" /> Mark Active
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
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

      {/* Dialogs */}
      <TodoForm
        mode="create"
        open={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />
      <TagManager
        open={showTagManager}
        onClose={() => setShowTagManager(false)}
      />
    </div>
  );
}
