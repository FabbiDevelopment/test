import { Plus, Tag as TagIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useTags } from "@/features/tags/api/tags";
import type { Todo } from "../api/todos";
import { useAttachTodoTag, useDetachTodoTag } from "../api/todos";

interface TodoTagDialogProps {
  todo: Todo | null;
  onClose: () => void;
}

export function TodoTagDialog({ todo, onClose }: TodoTagDialogProps) {
  const { data: allTags = [], isLoading } = useTags(todo?.user_id);
  const attachTag = useAttachTodoTag();
  const detachTag = useDetachTodoTag();
  const attachedTags = todo?.tags ?? [];
  const attachedTagIds = new Set(attachedTags.map((tag) => tag.id));
  const availableTags = allTags.filter((tag) => !attachedTagIds.has(tag.id));
  const isPending = attachTag.isPending || detachTag.isPending;

  const attach = (tagId: string) => {
    if (!todo) {
      return;
    }
    attachTag.mutate({ todoId: todo.id, tagId, userId: todo.user_id });
  };

  const detach = (tagId: string) => {
    if (!todo) {
      return;
    }
    detachTag.mutate({ todoId: todo.id, tagId, userId: todo.user_id });
  };

  return (
    <Dialog open={Boolean(todo)} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Tags for {todo?.title}</DialogTitle>
          <DialogDescription>
            Add a tag to group this work, or remove one that no longer applies.
          </DialogDescription>
        </DialogHeader>

        <section className="space-y-2" aria-labelledby="todo-attached-tags">
          <h3 id="todo-attached-tags" className="text-sm font-medium">
            On this Todo
          </h3>
          {attachedTags.length === 0 ? (
            <p className="rounded-md border border-dashed px-3 py-2 text-sm text-muted-foreground">
              No tags yet.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {attachedTags.map((tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-medium"
                  style={{ borderColor: tag.color || "#94a3b8", color: tag.color || "#475569" }}
                >
                  <span
                    className="size-1.5 rounded-full"
                    style={{ backgroundColor: tag.color || "#64748b" }}
                    aria-hidden="true"
                  />
                  {tag.name}
                  <button
                    type="button"
                    className="rounded-full p-0.5 hover:bg-black/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    aria-label={`Remove ${tag.name}`}
                    disabled={isPending}
                    onClick={() => detach(tag.id)}
                  >
                    <X className="size-3" aria-hidden="true" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </section>

        <section className="space-y-2" aria-labelledby="todo-available-tags">
          <h3 id="todo-available-tags" className="text-sm font-medium">
            Available tags
          </h3>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading tags…</p>
          ) : availableTags.length === 0 ? (
            <p className="rounded-md bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
              {allTags.length === 0
                ? "Create a tag from Manage tags before adding it here."
                : "All of your tags are already on this Todo."}
            </p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              {availableTags.map((tag) => (
                <Button
                  key={tag.id}
                  type="button"
                  variant="outline"
                  size="sm"
                  className="justify-start"
                  disabled={isPending}
                  onClick={() => attach(tag.id)}
                >
                  <TagIcon className="size-3.5" style={{ color: tag.color || "#64748b" }} />
                  <span className="min-w-0 flex-1 truncate text-left">{tag.name}</span>
                  <Plus className="size-3.5" aria-hidden="true" />
                </Button>
              ))}
            </div>
          )}
        </section>
      </DialogContent>
    </Dialog>
  );
}
