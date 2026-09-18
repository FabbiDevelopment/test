import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTodos, useBulkUpdateStatus, useTags } from "../api/todos";
import type { TodoFilters } from "../api/todos";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TagManager } from "./TagManager";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<TodoFilters>({ page: 1, page_size: 20 });
  const invalidDates = !!(filters.date_from && filters.date_to && filters.date_from > filters.date_to);
  const params = {
    ...filters,
    date_from: filters.date_from ? new Date(`${filters.date_from}T00:00:00`).toISOString() : undefined,
    date_to: filters.date_to ? new Date(`${filters.date_to}T23:59:59.999`).toISOString() : undefined,
  };
  const { data, isLoading, isFetching, error } = useTodos(params, !invalidDates);
  const { data: tags = [] } = useTags();
  const { user, logout } = useAuth();
  const bulk = useBulkUpdateStatus();
  const visibleSelected = new Set(data?.items.filter((item) => selected.has(item.id)).map((item) => item.id) ?? []);
  const allSelected = !!data?.items.length && data.items.every((item) => visibleSelected.has(item.id));
  const changeFilters = (patch: Partial<TodoFilters>) => {
    setFilters((old) => ({ ...old, ...patch, page: patch.page ?? 1 }));
    setSelected(new Set());
  };
  const hasFilters = filters.status !== undefined || filters.keyword || filters.tag_id || filters.date_from || filters.date_to;
  const applyBulk = (completed: boolean) => bulk.mutate(
    { todo_ids: [...visibleSelected], completed }, { onSuccess: () => setSelected(new Set()) },
  );
  return <div className="min-h-screen bg-muted/40">
    <header className="bg-card border-b">
      <div className="max-w-4xl mx-auto p-4 flex justify-between gap-3 items-center">
        <div><h1 className="text-xl font-bold">Todo App</h1><p className="text-sm text-muted-foreground">{user?.email}</p></div>
        <div className="flex gap-2"><Button variant="outline" onClick={() => setTagsOpen(true)}>Manage tags</Button>
          <Button variant="ghost" onClick={logout}>Logout</Button></div>
      </div>
    </header>
    <main className="max-w-4xl mx-auto p-4 md:py-8">
      <div className="rounded-xl border bg-card p-5 space-y-5">
        <div className="flex items-center justify-between"><h2 className="font-semibold text-lg">My Todos</h2>
          <Button onClick={() => setCreateOpen(true)}>Add Todo</Button></div>
        <section aria-label="Todo filters" className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1"><Label htmlFor="search">Keyword</Label><Input id="search" maxLength={100} placeholder="Search todos..."
            value={filters.keyword ?? ""} onChange={(event) => changeFilters({ keyword: event.target.value || undefined })} /></div>
          <div className="space-y-1"><Label htmlFor="status">Status</Label><select id="status" className="border rounded h-9 w-full bg-background px-2"
            value={filters.status === undefined ? "all" : String(filters.status)}
            onChange={(event) => changeFilters({ status: event.target.value === "all" ? undefined : event.target.value === "true" })}>
            <option value="all">All</option><option value="false">Active</option><option value="true">Completed</option>
          </select></div>
          <div className="space-y-1"><Label htmlFor="tag-filter">Tag</Label><select id="tag-filter" className="border rounded h-9 w-full bg-background px-2"
            value={filters.tag_id ?? ""} onChange={(event) => changeFilters({ tag_id: event.target.value || undefined })}>
            <option value="">All tags</option>{tags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
          </select></div>
          <div className="space-y-1"><Label htmlFor="date-from">From date</Label><Input id="date-from" type="date" value={filters.date_from ?? ""}
            max={filters.date_to} onChange={(event) => changeFilters({ date_from: event.target.value || undefined })} /></div>
          <div className="space-y-1"><Label htmlFor="date-to">To date</Label><Input id="date-to" type="date" value={filters.date_to ?? ""}
            min={filters.date_from} onChange={(event) => changeFilters({ date_to: event.target.value || undefined })} /></div>
          {hasFilters && <Button variant="outline" className="self-end" onClick={() => { setFilters({ page: 1, page_size: 20 }); setSelected(new Set()); }}>Clear filters</Button>}
        </section>
        {invalidDates && <p role="alert">From date must not be after To date.</p>}
        {isLoading && <p role="status">Loading todos...</p>}
        {error && <p role="alert" className="text-destructive">Failed to load todos. Please try again.</p>}
        {data && !invalidDates && <>
          {data.items.length > 0 && <div className="flex flex-wrap gap-2 items-center">
            <Button variant="outline" size="sm" disabled={bulk.isPending || isFetching}
              onClick={() => setSelected(allSelected ? new Set() : new Set(data.items.map((item) => item.id)))}>
              {allSelected ? "Deselect page" : "Select page"}</Button>
            {visibleSelected.size > 0 && <><span>{visibleSelected.size} selected</span>
              <Button size="sm" disabled={bulk.isPending || isFetching} onClick={() => applyBulk(true)}>Mark completed</Button>
              <Button size="sm" variant="outline" disabled={bulk.isPending || isFetching} onClick={() => applyBulk(false)}>Mark active</Button></>}
          </div>}
          <TodoList todos={data.items} selectedIds={visibleSelected} busy={bulk.isPending || isFetching}
            onSelectChange={(id, checked) => setSelected((old) => { const next = new Set(old); if (checked) next.add(id); else next.delete(id); return next; })}
            onDelete={() => changeFilters({ page: 1 })} />
          <div className="flex justify-center items-center gap-3">
            <Button variant="outline" size="sm" disabled={(filters.page ?? 1) <= 1 || isFetching} onClick={() => changeFilters({ page: (filters.page ?? 1) - 1 })}>Previous</Button>
            <span className="text-sm" data-testid="pagination">Page {filters.page ?? 1} · {data.total} total</span>
            <Button variant="outline" size="sm" disabled={(filters.page ?? 1) * (filters.page_size ?? 20) >= data.total || isFetching}
              onClick={() => changeFilters({ page: (filters.page ?? 1) + 1 })}>Next</Button>
          </div>
        </>}
      </div>
    </main>
    <TodoForm mode="create" open={createOpen} onClose={() => { setCreateOpen(false); changeFilters({ page: 1 }); }} />
    <TagManager open={tagsOpen} onClose={() => setTagsOpen(false)} />
  </div>;
}
