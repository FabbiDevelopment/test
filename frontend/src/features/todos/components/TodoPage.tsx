import { useState } from "react";
import { Plus, LogOut, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useTodos, type TodoFilterParams } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { FilterBar } from "./FilterBar";
import { TagManagerModal } from "@/features/tags/components/TagManagerModal";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTagModal, setShowTagModal] = useState(false);
  const [filters, setFilters] = useState<TodoFilterParams>({
    page: 1,
    size: 20,
  });

  const { data, isLoading, error } = useTodos(filters);
  const { user, logout } = useAuth();

  const handleClearFilters = () => {
    setFilters({ page: 1, size: 20 });
  };

  const totalPages = data ? Math.ceil(data.total / data.size) : 1;

  return (
    <div className="min-h-screen bg-muted/40 pb-20">
      {/* Header */}
      <header className="bg-card border-b sticky top-0 z-30 shadow-2xs">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-tight">Todo Master App</h1>
            {user && (
              <p className="text-xs text-muted-foreground">{user.email}</p>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={logout} className="text-xs h-8">
            <LogOut className="h-3.5 w-3.5 mr-1.5" />
            Đăng xuất
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <Card className="shadow-xs border-border/60">
          <CardHeader className="flex flex-row items-center justify-between py-4">
            <CardTitle className="text-base font-bold">Danh sách công việc</CardTitle>
            <Button size="sm" onClick={() => setShowCreateForm(true)} className="h-8 gap-1 text-xs">
              <Plus className="h-3.5 w-3.5" />
              <span>Tạo công việc</span>
            </Button>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4 space-y-4">
            {/* Filter Bar Component */}
            <FilterBar
              filters={filters}
              onFilterChange={(newFilters) => setFilters(newFilters)}
              onClearFilters={handleClearFilters}
              onOpenTagManager={() => setShowTagModal(true)}
            />

            {isLoading && (
              <div className="text-center py-12 text-muted-foreground text-sm">
                Đang tải danh sách công việc...
              </div>
            )}

            {error && (
              <div className="text-center py-12 text-destructive text-sm">
                Không thể tải danh sách công việc. Vui lòng thử lại.
              </div>
            )}

            {data && <TodoList todos={data.items} />}

            {/* Pagination Controls */}
            {data && data.total > 0 && (
              <div className="flex flex-wrap items-center justify-between gap-2 mt-4 pt-4 border-t text-xs text-muted-foreground">
                <span>
                  Hiển thị {data.items.length} trên tổng số {data.total} công việc
                </span>

                {totalPages > 1 && (
                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={filters.page === 1}
                      onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                      className="h-7 px-2"
                    >
                      <ChevronLeft className="h-3.5 w-3.5 mr-1" />
                      Trang trước
                    </Button>
                    <span className="px-2 font-medium">
                      {filters.page} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={filters.page === totalPages}
                      onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                      className="h-7 px-2"
                    >
                      Trang sau
                      <ChevronRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Create Todo Modal */}
      <TodoForm
        mode="create"
        open={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />

      {/* Tag Manager Modal */}
      <TagManagerModal
        open={showTagModal}
        onClose={() => setShowTagModal(false)}
      />
    </div>
  );
}
