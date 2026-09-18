import { useState } from "react";
import { CheckCheck, ChevronLeft, ChevronRight, LogOut, Plus, Tags, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useBulkStatus, useTags, useTodos } from "../api/todos";
import type { TodoFilters } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TagManager } from "./TagManager";
import { useAuth } from "@/features/auth/hooks/useAuth";

const PAGE_SIZE = 20;
const initialFilters: TodoFilters = { page: 1, page_size: PAGE_SIZE, status: "all" };

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTags, setShowTags] = useState(false);
  const [filters, setFilters] = useState<TodoFilters>(initialFilters);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { data, isLoading, error } = useTodos(filters);
  const { data: tags = [] } = useTags();
  const bulk = useBulkStatus();
  const { user, logout } = useAuth();
  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE));
  const updateFilter = (patch: Partial<TodoFilters>) => { setFilters(current => ({ ...current, ...patch, page: patch.page ?? 1 })); setSelected(new Set()); };
  const bulkUpdate = (completed: boolean) => bulk.mutate({ todoIds: [...selected], completed }, { onSuccess: () => setSelected(new Set()) });

  return <div className="min-h-screen bg-muted/40">
    <header className="border-b bg-card"><div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4"><div><h1 className="text-xl font-bold">Todo App</h1>{user && <p className="text-sm text-muted-foreground">{user.email}</p>}</div><Button variant="ghost" size="sm" onClick={logout}><LogOut className="mr-2 size-4" />Logout</Button></div></header>
    <main className="mx-auto max-w-5xl px-4 py-8"><Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-lg">My Todos</CardTitle><div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => setShowTags(true)}><Tags className="mr-1 size-4" />Tags</Button><Button size="sm" onClick={() => setShowCreateForm(true)}><Plus className="mr-1 size-4" />Add Todo</Button></div></CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
          <Input className="lg:col-span-2" aria-label="Search todos" placeholder="Search title or description" value={filters.keyword || ""} onChange={e => updateFilter({ keyword: e.target.value || undefined })} />
          <select aria-label="Status" className="h-9 rounded-md border bg-background px-3 text-sm" value={filters.status} onChange={e => updateFilter({ status: e.target.value as TodoFilters["status"] })}><option value="all">All status</option><option value="active">Active</option><option value="completed">Completed</option></select>
          <select aria-label="Tag" className="h-9 rounded-md border bg-background px-3 text-sm" value={filters.tag_id || ""} onChange={e => updateFilter({ tag_id: e.target.value || undefined })}><option value="">All tags</option>{tags.map(tag => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select>
          <Input aria-label="From date" type="date" value={filters.date_from?.slice(0, 10) || ""} onChange={e => updateFilter({ date_from: e.target.value ? `${e.target.value}T00:00:00Z` : undefined })} />
          <Input aria-label="To date" type="date" value={filters.date_to?.slice(0, 10) || ""} onChange={e => updateFilter({ date_to: e.target.value ? `${e.target.value}T23:59:59Z` : undefined })} />
        </div>
        <div className="mb-4 flex min-h-9 items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => { setFilters(initialFilters); setSelected(new Set()); }}><X className="mr-1 size-4" />Clear filters</Button>
          {!!selected.size && <div className="flex items-center gap-2 text-sm"><span>{selected.size} selected</span><Button size="sm" variant="outline" onClick={() => bulkUpdate(false)}>Mark active</Button><Button size="sm" onClick={() => bulkUpdate(true)}><CheckCheck className="mr-1 size-4" />Complete</Button></div>}
        </div>
        {isLoading && <div className="py-12 text-center text-muted-foreground">Loading todos...</div>}
        {error && <div className="py-12 text-center text-destructive">Failed to load todos.</div>}
        {data && <TodoList todos={data.items} tags={tags} selected={selected} onSelectionChange={setSelected} />}
        {data && data.total > 0 && <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground"><span>Page {filters.page} of {totalPages} ({data.total} todos)</span><div className="flex gap-1"><Button variant="outline" size="icon" aria-label="Previous page" disabled={filters.page === 1} onClick={() => updateFilter({ page: filters.page - 1 })}><ChevronLeft className="size-4" /></Button><Button variant="outline" size="icon" aria-label="Next page" disabled={filters.page >= totalPages} onClick={() => updateFilter({ page: filters.page + 1 })}><ChevronRight className="size-4" /></Button></div></div>}
      </CardContent>
    </Card></main>
    <TodoForm mode="create" open={showCreateForm} onClose={() => setShowCreateForm(false)} />
    <TagManager open={showTags} onClose={() => setShowTags(false)} />
  </div>;
}