import { useState } from "react";
import { Pencil, Trash2, Tags as TagsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useTags, useDeleteTag, type Tag } from "../api/tags";
import { TagForm } from "./TagForm";

interface TagManagerDialogProps {
  open: boolean;
  onClose: () => void;
}

export function TagManagerDialog({ open, onClose }: TagManagerDialogProps) {
  const { data: tags, isLoading } = useTags();
  const deleteTag = useDeleteTag();
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    deleteTag.mutate(id, { onSuccess: () => setConfirmDeleteId(null) });
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagsIcon className="h-4 w-4" />
            Manage Tags
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          {isLoading && (
            <p className="text-sm text-muted-foreground">Loading tags...</p>
          )}

          {tags && tags.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No tags yet. Create one below.
            </p>
          )}

          <div className="space-y-1 max-h-56 overflow-y-auto">
            {tags?.map((tag) =>
              editingTag?.id === tag.id ? (
                <div key={tag.id} className="rounded-md border p-2">
                  <TagForm
                    mode="edit"
                    tag={tag}
                    onDone={() => setEditingTag(null)}
                  />
                </div>
              ) : (
                <div
                  key={tag.id}
                  className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-accent/50"
                >
                  <Badge
                    style={{
                      borderColor: tag.color ?? undefined,
                      color: tag.color ?? undefined,
                    }}
                  >
                    {tag.name}
                  </Badge>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setEditingTag(tag)}
                      aria-label={`Rename ${tag.name}`}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    {confirmDeleteId === tag.id ? (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="destructive"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={() => handleDelete(tag.id)}
                        >
                          Confirm
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={() => setConfirmDeleteId(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => setConfirmDeleteId(tag.id)}
                        aria-label={`Delete ${tag.name}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              )
            )}
          </div>

          <Separator />

          <div>
            <p className="text-sm font-medium mb-2">New tag</p>
            <TagForm mode="create" onDone={() => {}} />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
