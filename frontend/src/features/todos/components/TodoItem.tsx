import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Pencil, Tags, Trash2 } from "lucide-react";
import { useState } from "react";
import type { Tag, Todo } from "../api/todos";
import { useSetTodoTag } from "../api/todos";

interface Props { todo: Todo; tags: Tag[]; selected: boolean; onSelect: (checked: boolean) => void; onToggle: (todo: Todo) => void; onEdit: (todo: Todo) => void; onDelete: (id: string) => void; }

export function TodoItem({ todo, tags, selected, onSelect, onToggle, onEdit, onDelete }: Props) {
  const [showTags, setShowTags] = useState(false);
  const setTag = useSetTodoTag();
  return <div className="flex items-start gap-3 rounded-md border bg-card p-3 transition-colors hover:bg-accent/50">
    <Checkbox aria-label="Select todo for bulk actions" checked={selected} onCheckedChange={value => onSelect(value === true)} />
    <Checkbox id={`todo-${todo.id}`} checked={todo.completed} onCheckedChange={() => onToggle(todo)} />
    <div className="min-w-0 flex-1">
      <label htmlFor={`todo-${todo.id}`} className={`cursor-pointer text-sm font-medium ${todo.completed ? "line-through text-muted-foreground" : ""}`}>{todo.title}</label>
      {todo.description && <p className="mt-0.5 truncate text-xs text-muted-foreground">{todo.description}</p>}
      {!!todo.tags?.length && <div className="mt-2 flex flex-wrap gap-1">{todo.tags.map(tag => <span key={tag.id} className="rounded px-1.5 py-0.5 text-xs text-white" style={{ backgroundColor: tag.color || "#64748b" }}>{tag.name}</span>)}</div>}
    </div>
    <div className="flex items-center gap-1">
      <Button variant="ghost" size="icon" title="Assign tags" onClick={() => setShowTags(true)}><Tags className="size-4" /></Button>
      <Button variant="ghost" size="icon" title="Edit todo" onClick={() => onEdit(todo)}><Pencil className="size-4" /></Button>
      <Button variant="ghost" size="icon" title="Delete todo" className="text-destructive" onClick={() => onDelete(todo.id)}><Trash2 className="size-4" /></Button>
    </div>
    <Dialog open={showTags} onOpenChange={setShowTags}><DialogContent><DialogHeader><DialogTitle>Tags for {todo.title}</DialogTitle></DialogHeader>
      <div className="space-y-3">{tags.map(tag => { const attached = todo.tags.some(item => item.id === tag.id); return <label key={tag.id} className="flex items-center gap-3 text-sm"><Checkbox checked={attached} onCheckedChange={() => setTag.mutate({ todoId: todo.id, tagId: tag.id, attached })} /><span className="size-3 rounded-full" style={{ backgroundColor: tag.color || "#64748b" }} />{tag.name}</label>; })}{!tags.length && <p className="text-sm text-muted-foreground">Create a tag first.</p>}</div>
    </DialogContent></Dialog>
  </div>;
}