import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Plus, X, Tag as TagIcon } from "lucide-react";
import {
  useTags,
  useCreateTag,
  useDeleteTag,
  useAttachTag,
  useDetachTag,
  type Todo,
  type Tag,
} from "../api/todos";

interface TodoTagDialogProps {
  todo: Todo | null;
  open: boolean;
  onClose: () => void;
}

export function TodoTagDialog({ todo, open, onClose }: TodoTagDialogProps) {
  const { data: allTags = [] } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3b82f6");

  if (!todo) return null;

  const todoTagIds = new Set(todo.tags?.map((t) => t.id) || []);

  const handleCreateTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    createTag.mutate(
      { name: newTagName.trim(), color: newTagColor },
      {
        onSuccess: () => setNewTagName(""),
      }
    );
  };

  const handleToggleTag = (tag: Tag) => {
    if (todoTagIds.has(tag.id)) {
      detachTag.mutate({ todo_id: todo.id, tag_id: tag.id });
    } else {
      attachTag.mutate({ todo_id: todo.id, tag_id: tag.id });
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5 text-primary" />
            Manage Tags for &quot;{todo.title}&quot;
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Available tags to attach/detach */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Select tags to attach:
            </p>
            {allTags.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">
                No tags created yet. Create one below!
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {allTags.map((tag) => {
                  const isAttached = todoTagIds.has(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => handleToggleTag(tag)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all cursor-pointer ${
                        isAttached
                          ? "ring-2 ring-primary ring-offset-1 font-semibold"
                          : "opacity-60 hover:opacity-100"
                      }`}
                      style={{
                        backgroundColor: tag.color ? `${tag.color}20` : "var(--muted)",
                        borderColor: tag.color || "var(--border)",
                        color: tag.color || "var(--foreground)",
                      }}
                    >
                      <span>{tag.name}</span>
                      {isAttached && <span className="text-xs">✓</span>}
                      <button
                        type="button"
                        className="ml-1 hover:text-destructive opacity-50 hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteTag.mutate(tag.id);
                        }}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Create new tag form */}
          <form onSubmit={handleCreateTag} className="border-t pt-4 space-y-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Create New Tag:
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="Tag name (e.g. Work, Urgent)..."
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className="flex-1"
              />
              <input
                type="color"
                value={newTagColor}
                onChange={(e) => setNewTagColor(e.target.value)}
                className="h-9 w-9 p-0.5 border rounded cursor-pointer"
                title="Choose color"
              />
              <Button type="submit" size="sm" disabled={!newTagName.trim() || createTag.isPending}>
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
