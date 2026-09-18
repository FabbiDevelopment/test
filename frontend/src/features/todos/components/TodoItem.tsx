import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, X } from "lucide-react";
import type { Tag, Todo } from "../api/todos";

interface Props { todo: Todo; selected: boolean; tags: Tag[]; onSelect: (id: string) => void; onToggle: (todo: Todo) => void; onEdit: (todo: Todo) => void; onDelete: (id: string) => void; onAttach: (todoId: string, tagId: string) => void; onDetach: (todoId: string, tagId: string) => void; }
export function TodoItem({ todo, selected, tags, onSelect, onToggle, onEdit, onDelete, onAttach, onDetach }: Props) {
  const attachable = tags.filter((tag) => !todo.tags.some((current) => current.id === tag.id));
  return <div className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
    <Checkbox aria-label={`Select ${todo.title}`} checked={selected} onCheckedChange={() => onSelect(todo.id)} />
    <Checkbox id={`todo-${todo.id}`} checked={todo.completed} onCheckedChange={() => onToggle(todo)} />
    <div className="flex-1 min-w-0"><label htmlFor={`todo-${todo.id}`} className={`text-sm font-medium cursor-pointer ${todo.completed ? "line-through text-muted-foreground" : ""}`}>{todo.title}</label>
      {todo.description && <p className="text-xs text-muted-foreground mt-0.5 truncate">{todo.description}</p>}
      <div className="flex flex-wrap gap-1 mt-2">{todo.tags.map((tag) => <span key={tag.id} className="inline-flex items-center rounded bg-muted px-2 py-0.5 text-xs" style={{ borderLeft: `3px solid ${tag.color || "#64748b"}` }}>{tag.name}<button aria-label={`Remove ${tag.name}`} className="ml-1" onClick={() => onDetach(todo.id, tag.id)}><X className="h-3 w-3" /></button></span>)}</div>
      {attachable.length > 0 && <select aria-label={`Add tag to ${todo.title}`} className="mt-2 text-xs border rounded px-1 py-0.5" defaultValue="" onChange={(event) => { if (event.target.value) { onAttach(todo.id, event.target.value); event.currentTarget.value = ""; } }}><option value="">Add tag…</option>{attachable.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select>}
    </div>
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(todo)} aria-label={`Edit ${todo.title}`}><Pencil className="h-3.5 w-3.5" /></Button><Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => onDelete(todo.id)} aria-label={`Delete ${todo.title}`}><Trash2 className="h-3.5 w-3.5" /></Button></div>
  </div>;
}
