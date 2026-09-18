import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { useTags, useAttachTag, useDetachTag } from "../api/todos";
import type { Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo; selected: boolean; pending: boolean;
  onSelectChange: (checked: boolean) => void;
  onToggle: () => void; onEdit: () => void; onDelete: () => void;
}

export function TodoItem({ todo, selected, pending, onSelectChange, onToggle, onEdit, onDelete }: TodoItemProps) {
  const { data: tags = [] } = useTags();
  const attach = useAttachTag(), detach = useDetachTag();
  const unusedTags = tags.filter((tag) => !todo.tags.some((attached) => attached.id === tag.id));
  return (
    <article data-testid="todo-item" className={`flex gap-3 p-3 rounded-lg border ${selected ? "bg-primary/5" : "bg-card"}`}>
      <Checkbox checked={selected} onCheckedChange={(value) => onSelectChange(!!value)} aria-label={`Select ${todo.title}`} disabled={pending} />
      <Checkbox id={`todo-${todo.id}`} checked={todo.completed} onCheckedChange={onToggle} disabled={pending}
        aria-label={`Complete ${todo.title}`} />
      <div className="flex-1 min-w-0 space-y-2">
        <label htmlFor={`todo-${todo.id}`} className={`font-medium cursor-pointer ${todo.completed ? "line-through text-muted-foreground" : ""}`}>
          {todo.title}
        </label>
        {todo.description && <p className="text-sm text-muted-foreground break-words">{todo.description}</p>}
        <div className="flex flex-wrap gap-2">
          {todo.tags.map((tag) => <span key={tag.id} className="rounded border px-2 text-xs inline-flex gap-1 items-center"
            style={{ borderColor: tag.color ?? undefined }}>
            {tag.name}
            <button aria-label={`Remove tag ${tag.name} from ${todo.title}`} disabled={detach.isPending || pending}
              onClick={() => detach.mutate({ todo_id: todo.id, tag_id: tag.id })}>×</button>
          </span>)}
        </div>
        {unusedTags.length > 0 && <select aria-label={`Add tag to ${todo.title}`} value="" disabled={attach.isPending || pending}
          className="border rounded px-2 py-1 text-sm bg-background"
          onChange={(event) => { if (event.target.value) attach.mutate({ todo_id: todo.id, tag_id: event.target.value }); }}>
          <option value="">Add tag...</option>
          {unusedTags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
        </select>}
      </div>
      <div className="flex flex-col gap-2">
        <Button size="sm" variant="outline" onClick={onEdit} disabled={pending} aria-label={`Edit ${todo.title}`}>Edit</Button>
        <Button size="sm" variant="outline" onClick={onDelete} disabled={pending} aria-label={`Delete ${todo.title}`}>Delete</Button>
      </div>
    </article>
  );
}
