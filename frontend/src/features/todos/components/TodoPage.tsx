import { useState } from "react";
import { Plus, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, type TodoFilters } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TodoFilterBar, EMPTY_FILTERS } from "./TodoFilterBar";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { TagManager } from "@/features/tags/components/TagManager";
import { useTags } from "@/features/tags/api/tags";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState<TodoFilters>({ ...EMPTY_FILTERS });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading, error } = useTodos(filters);
  const { data: tags = [] } = useTags();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-muted/40">
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

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-4">
        <TagManager />

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
            {/* THÊM: filter bar — Level 4 */}
            <TodoFilterBar
              filters={filters}
              tags={tags}
              onChange={setFilters}
              onClear={() => setFilters({ ...EMPTY_FILTERS })}
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
                tags={tags}
                selectedIds={selectedIds}
                onSelectChange={setSelectedIds}
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

      <TodoForm
        mode="create"
        open={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />
    </div>
  );
}
