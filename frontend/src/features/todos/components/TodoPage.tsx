import { useState } from "react";
import { Plus, LogOut, Search, CheckSquare, Square, Check, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, useTags, useBulkUpdateStatus } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedTagId, setSelectedTagId] = useState<string>("all");
  const [keyword, setKeyword] = useState<string>("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const { data: tags = [] } = useTags();
  const bulkUpdateStatus = useBulkUpdateStatus();

  const { data, isLoading, error } = useTodos({
    status: statusFilter,
    tag_id: selectedTagId,
    keyword: keyword.trim() || undefined,
  });

  const { user, logout } = useAuth();

  const handleSelectToggle = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (!data?.items) return;
    if (selectedIds.size === data.items.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.items.map((t) => t.id)));
    }
  };

  const handleBulkStatus = (completed: boolean) => {
    if (selectedIds.size === 0) return;
    bulkUpdateStatus.mutate(
      { todo_ids: Array.from(selectedIds), completed },
      {
        onSuccess: () => setSelectedIds(new Set()),
      }
    );
  };

  const handleClearFilters = () => {
    setStatusFilter("all");
    setSelectedTagId("all");
    setKeyword("");
  };

  const isFiltered = statusFilter !== "all" || selectedTagId !== "all" || keyword.trim() !== "";

  return (
    <div className="min-h-screen bg-muted/40">
      {/* Header */}
      <header className="bg-card border-b sticky top-0 z-10 shadow-xs">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Todo App</h1>
            {user && (
              <p className="text-xs text-muted-foreground">{user.email}</p>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        {/* Filter Bar */}
        <Card className="p-3">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search todos by keyword..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="pl-8 text-sm"
              />
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {/* Status Tabs */}
              <div className="inline-flex rounded-lg border p-1 bg-muted/50 text-xs">
                {(["all", "active", "completed"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                      statusFilter === st
                        ? "bg-background text-foreground shadow-xs"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              {/* Tag selector */}
              {tags.length > 0 && (
                <select
                  value={selectedTagId}
                  onChange={(e) => setSelectedTagId(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-hidden"
                >
                  <option value="all">All Tags</option>
                  {tags.map((tag) => (
                    <option key={tag.id} value={tag.id}>
                      {tag.name}
                    </option>
                  ))}
                </select>
              )}

              {isFiltered && (
                <Button variant="ghost" size="sm" onClick={handleClearFilters} className="text-xs h-8">
                  <RotateCcw className="h-3 w-3 mr-1" />
                  Reset
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* Bulk Actions Toolbar */}
        {data && data.items.length > 0 && (
          <div className="flex items-center justify-between px-2 py-1 text-xs text-muted-foreground bg-muted/30 rounded-md border">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs px-2"
                onClick={handleSelectAll}
              >
                {selectedIds.size === data.items.length && data.items.length > 0 ? (
                  <CheckSquare className="h-3.5 w-3.5 mr-1" />
                ) : (
                  <Square className="h-3.5 w-3.5 mr-1" />
                )}
                {selectedIds.size > 0 ? `${selectedIds.size} Selected` : "Select All"}
              </Button>
            </div>

            {selectedIds.size > 0 && (
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => handleBulkStatus(true)}
                  disabled={bulkUpdateStatus.isPending}
                >
                  <Check className="h-3 w-3 mr-1 text-green-600" />
                  Mark Completed
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => handleBulkStatus(false)}
                  disabled={bulkUpdateStatus.isPending}
                >
                  Mark Active
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Todos Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base font-semibold">My Todos</CardTitle>
            <Button size="sm" onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Add Todo
            </Button>
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
                onSelectToggle={handleSelectToggle}
              />
            )}

            {data && data.total > 0 && (
              <div className="mt-4 text-center text-xs text-muted-foreground">
                Showing {data.items.length} of {data.total} todos
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
