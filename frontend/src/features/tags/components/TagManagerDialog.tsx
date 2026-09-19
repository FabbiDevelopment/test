import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Plus, Tag as TagIcon, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTag, useDeleteTag, useTags, useUpdateTag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";
import type { Tag } from "../types";

interface TagManagerDialogProps {
  open: boolean;
  onClose: () => void;
  userId: string | undefined;
}

export function TagManagerDialog({
  open,
  onClose,
  userId,
}: TagManagerDialogProps) {
  const { data: tags = [], isLoading } = useTags(userId);
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: { name: "", color: "" },
  });

  const submitTag = (data: TagFormData) => {
    if (editingTag) {
      updateTag.mutate(
        { id: editingTag.id, data },
        {
          onSuccess: () => {
            setEditingTag(null);
            reset({ name: "", color: "" });
          },
        },
      );
      return;
    }

    createTag.mutate(data, { onSuccess: () => reset({ name: "", color: "" }) });
  };

  const startEditing = (tag: Tag) => {
    setEditingTag(tag);
    reset({ name: tag.name, color: tag.color ?? "" });
  };

  const cancelEditing = () => {
    setEditingTag(null);
    reset({ name: "", color: "" });
  };

  const close = () => {
    cancelEditing();
    onClose();
  };

  const isPending = createTag.isPending || updateTag.isPending;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && close()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Manage tags</DialogTitle>
          <DialogDescription>
            Use tags to group related work. Names are private to your account.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(submitTag)} className="rounded-lg border bg-muted/30 p-3">
          <div className="grid gap-3 sm:grid-cols-[1fr_9rem_auto] sm:items-end">
            <div className="space-y-1.5">
              <Label htmlFor="tag-name">Tag name</Label>
              <Input id="tag-name" placeholder="e.g. Client work" {...register("name")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tag-color">Color (optional)</Label>
              <Input id="tag-color" placeholder="#64748b" {...register("color")} />
            </div>
            <Button type="submit" size="sm" disabled={isPending}>
              {editingTag ? <Pencil /> : <Plus />}
              {editingTag ? "Save" : "Add"}
            </Button>
          </div>
          {(errors.name || errors.color) && (
            <p className="mt-2 text-xs text-destructive">
              {errors.name?.message ?? errors.color?.message}
            </p>
          )}
          {editingTag && (
            <Button type="button" variant="ghost" size="xs" className="mt-2" onClick={cancelEditing}>
              Cancel rename
            </Button>
          )}
        </form>

        <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
          {isLoading && <p className="py-6 text-center text-sm text-muted-foreground">Loading tags…</p>}
          {!isLoading && tags.length === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Create a tag to start grouping your work.
            </p>
          )}
          {tags.map((tag) => (
            <div key={tag.id} className="flex items-center gap-3 rounded-md border px-3 py-2">
              <span
                className="h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: tag.color || "#64748b" }}
                aria-hidden="true"
              />
              <TagIcon className="h-4 w-4 text-muted-foreground" />
              <span className="min-w-0 flex-1 truncate text-sm font-medium">{tag.name}</span>
              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                aria-label={`Rename ${tag.name}`}
                onClick={() => startEditing(tag)}
              >
                <Pencil />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                className="text-destructive hover:text-destructive"
                aria-label={`Delete ${tag.name}`}
                disabled={deleteTag.isPending}
                onClick={() => userId && deleteTag.mutate({ id: tag.id, userId })}
              >
                <Trash2 />
              </Button>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
