import { useState } from "react";
import { Plus, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useTodos, type TodoFilters } from "../api/todos";
import { useTags } from "../api/tags";
import { TodoList } from "./TodoList";
import { TodoForm } from "./TodoForm";
import { TagManager } from "./TagManager";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false); const [filters, setFilters] = useState<TodoFilters>({});
  const { data, isLoading, error } = useTodos(filters); const { data: tags = [] } = useTags(); const { user, logout } = useAuth();
  const update = (changes: TodoFilters) => setFilters((old) => ({ ...old, ...changes }));
  const dateValue = (value: string | undefined) => value ? new Date(value).toLocaleDateString("en-CA") : "";
  const localDayBoundary = (day: string, endOfDay = false) => new Date(`${day}T${endOfDay ? "23:59:59.999" : "00:00:00.000"}`).toISOString();
  return <div className="min-h-screen bg-muted/40"><header className="bg-card border-b"><div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between"><div><h1 className="text-xl font-bold">Todo App</h1>{user && <p className="text-sm text-muted-foreground">{user.email}</p>}</div><Button variant="ghost" size="sm" onClick={logout}><LogOut className="h-4 w-4 mr-2" />Logout</Button></div></header><main className="max-w-3xl mx-auto px-4 py-8"><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-lg">My Todos</CardTitle><Button size="sm" onClick={() => setShowCreateForm(true)}><Plus className="h-4 w-4 mr-1" />Add Todo</Button></CardHeader><Separator /><CardContent className="pt-4"><div className="grid gap-2 md:grid-cols-4 mb-4"><Input aria-label="Search todos" placeholder="Keyword" value={filters.keyword || ""} onChange={(event) => update({ keyword: event.target.value || undefined })}/><select aria-label="Filter status" className="border rounded px-2" value={filters.completed === undefined ? "" : String(filters.completed)} onChange={(event) => update({ completed: event.target.value === "" ? undefined : event.target.value === "true" })}><option value="">All statuses</option><option value="false">Active</option><option value="true">Completed</option></select><select aria-label="Filter tag" className="border rounded px-2" value={filters.tag_id || ""} onChange={(event) => update({ tag_id: event.target.value || undefined })}><option value="">All tags</option>{tags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select><Button variant="outline" onClick={() => setFilters({})}>Clear filters</Button><Input aria-label="From date" type="date" value={dateValue(filters.date_from)} onChange={(event) => update({ date_from: event.target.value ? localDayBoundary(event.target.value) : undefined })}/><Input aria-label="To date" type="date" value={dateValue(filters.date_to)} onChange={(event) => update({ date_to: event.target.value ? localDayBoundary(event.target.value, true) : undefined })}/></div><TagManager tags={tags} />{isLoading && <div className="text-center py-12 text-muted-foreground">Loading todos...</div>}{error && <div className="text-center py-12 text-destructive">Failed to load todos. Please try again.</div>}{data && <TodoList todos={data.items} tags={tags} />}{data && <div className="mt-4 text-center text-sm text-muted-foreground">Showing {data.items.length} of {data.total} todos</div>}</CardContent></Card></main><TodoForm mode="create" open={showCreateForm} onClose={() => setShowCreateForm(false)} /></div>;
}
