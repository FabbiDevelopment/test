import { useState } from "react";
import { Plus, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTags } from "../api/tags";
import {
  defaultTodoFilters,
  useTodos,
  type TodoFilters,
} from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TodoFiltersBar } from "./TodoFilters";
import { TagManager } from "./TagManager";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState<TodoFilters>(defaultTodoFilters);
  const { data, isLoading, error } = useTodos(filters);
  const { data: tags = [] } = useTags();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-muted/40">
      {/* Header */}
      <header className="bg-card border-b">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
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
      <main className="max-w-5xl mx-auto px-4 py-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">My Todos</CardTitle>
            <div className="flex gap-2">
              <TagManager tags={tags} />
              <Button size="sm" onClick={() => setShowCreateForm(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Add Todo
              </Button>
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
            <TodoFiltersBar
              filters={filters}
              tags={tags}
              onChange={setFilters}
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

            {data && <TodoList todos={data.items} tags={tags} />}

            {data && data.total > 0 && (
              <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.page === 1}
                  onClick={() =>
                    setFilters((current) => ({
                      ...current,
                      page: current.page - 1,
                    }))
                  }
                >
                  Previous
                </Button>
                <span>
                  Page {filters.page} · Showing {data.items.length} of{" "}
                  {data.total}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.page * filters.pageSize >= data.total}
                  onClick={() =>
                    setFilters((current) => ({
                      ...current,
                      page: current.page + 1,
                    }))
                  }
                >
                  Next
                </Button>
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
    </div>
  );
}
