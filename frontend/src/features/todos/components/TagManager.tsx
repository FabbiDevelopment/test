import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Tags, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateTag,
  useDeleteTag,
  useUpdateTag,
  type Tag,
} from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/todo";

interface TagManagerProps {
  tags: Tag[];
}

const emptyTag: TagFormData = { name: "", color: "#2563eb" };

export function TagManager({ tags }: TagManagerProps) {
  const [open, setOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: emptyTag,
  });

  useEffect(() => {
    reset(
      editingTag
        ? { name: editingTag.name, color: editingTag.color ?? "#2563eb" }
        : emptyTag,
    );
  }, [editingTag, reset]);

  const submit = (data: TagFormData) => {
    const mutation = editingTag
      ? updateTag.mutateAsync({ id: editingTag.id, data })
      : createTag.mutateAsync(data);
    void mutation
      .then(() => {
        setEditingTag(null);
        reset(emptyTag);
      })
      .catch(() => undefined);
  };

  const close = () => {
    setOpen(false);
    setEditingTag(null);
    reset(emptyTag);
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <Tags className="mr-2 h-4 w-4" />
        Manage Tags
      </Button>

      <Dialog open={open} onOpenChange={(value) => !value && close()}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Manage Tags</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit(submit)} className="space-y-3">
            <div className="grid grid-cols-[1fr_72px] gap-3">
              <div className="space-y-1">
                <Label htmlFor="tag-name">Tag name</Label>
                <Input id="tag-name" {...register("name")} />
                {errors.name && (
                  <p className="text-xs text-destructive">
                    {errors.name.message}
                  </p>
                )}
              </div>
              <div className="space-y-1">
                <Label htmlFor="tag-color">Color</Label>
                <Input
                  id="tag-color"
                  type="color"
                  className="px-1"
                  {...register("color")}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              {editingTag && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditingTag(null)}
                >
                  Cancel edit
                </Button>
              )}
              <Button
                type="submit"
                disabled={createTag.isPending || updateTag.isPending}
              >
                {editingTag ? "Save tag" : "Create tag"}
              </Button>
            </div>
          </form>

          <div className="max-h-64 space-y-2 overflow-auto border-t pt-4">
            {tags.length === 0 && (
              <p className="text-sm text-muted-foreground">No tags yet.</p>
            )}
            {tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between rounded-md border p-2"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: tag.color ?? "#64748b" }}
                  />
                  <span className="text-sm font-medium">{tag.name}</span>
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Edit ${tag.name}`}
                    onClick={() => setEditingTag(tag)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${tag.name}`}
                    onClick={() => {
                      if (window.confirm(`Delete tag “${tag.name}”?`)) {
                        deleteTag.mutate(tag.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
