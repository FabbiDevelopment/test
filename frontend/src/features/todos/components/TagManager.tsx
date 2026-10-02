import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateTag,
  useDeleteTag,
  useTags,
  useUpdateTag,
  type Tag,
} from "../api/todos";
import { tagSchema, type TagFormData } from "../schemas/todo";

const defaultValues: TagFormData = { name: "", color: "" };

interface TagManagerProps {
  onTagDeleted: (tagId: string) => void;
}

export function TagManager({ onTagDeleted }: TagManagerProps) {
  const { data: tags = [], isLoading, error } = useTags();
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
    defaultValues,
  });
  const [editingTag, setEditingTag] = useState<Tag | null>(null);

  const closeEdit = () => {
    setEditingTag(null);
    reset(defaultValues);
  };

  const onSubmit = (values: TagFormData) => {
    const data = { name: values.name, color: values.color || null };
    if (editingTag) {
      updateTag.mutate(
        { id: editingTag.id, data },
        { onSuccess: closeEdit }
      );
      return;
    }
    createTag.mutate(data, { onSuccess: () => reset(defaultValues) });
  };

  const startEdit = (tag: Tag) => {
    setEditingTag(tag);
    reset({ name: tag.name, color: tag.color ?? "" });
  };

  const isPending = createTag.isPending || updateTag.isPending;

  return (
    <details className="rounded-md border p-4">
      <summary className="cursor-pointer text-sm font-semibold">
        Manage tags
      </summary>

      <div className="mt-4 space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <h2 className="text-sm font-medium">
            {editingTag ? "Edit tag" : "Create tag"}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="tag-name">Name</Label>
              <Input
                id="tag-name"
                maxLength={50}
                placeholder="Work"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-sm text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tag-color">Color (optional)</Label>
              <Input
                id="tag-color"
                maxLength={20}
                placeholder="#2563eb or blue"
                {...register("color")}
              />
              {errors.color && (
                <p className="text-sm text-destructive">
                  {errors.color.message}
                </p>
              )}
            </div>
          </div>
          <div className="flex justify-end gap-2">
            {editingTag && (
              <Button type="button" variant="outline" onClick={closeEdit}>
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={isPending}>
              {isPending
                ? "Saving..."
                : editingTag
                  ? "Save tag"
                  : "Create tag"}
            </Button>
          </div>
        </form>

        <div className="space-y-2">
          <h2 className="text-sm font-medium">Your tags</h2>
          {isLoading && (
            <p className="text-sm text-muted-foreground">Loading tags...</p>
          )}
          {error && (
            <p className="text-sm text-destructive">Failed to load tags.</p>
          )}
          {!isLoading && !error && tags.length === 0 && (
            <p className="text-sm text-muted-foreground">No tags yet.</p>
          )}
          {tags.map((tag) => (
            <TagRow
              key={tag.id}
              tag={tag}
              isDeleting={deleteTag.isPending}
              onEdit={startEdit}
              onDelete={() =>
                deleteTag.mutate(tag.id, {
                  onSuccess: () => onTagDeleted(tag.id),
                })
              }
            />
          ))}
        </div>
      </div>
    </details>
  );
}

interface TagRowProps {
  tag: Tag;
  isDeleting: boolean;
  onEdit: (tag: Tag) => void;
  onDelete: () => void;
}

function TagRow({ tag, isDeleting, onEdit, onDelete }: TagRowProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
      <span className="flex items-center gap-2 text-sm">
        <span
          aria-hidden="true"
          className="size-3 rounded-full border"
          style={{ backgroundColor: tag.color ?? "transparent" }}
        />
        {tag.name}
      </span>
      <div className="flex gap-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={`Edit ${tag.name}`}
          onClick={() => onEdit(tag)}
        >
          <Pencil className="size-4" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={`Delete ${tag.name}`}
          disabled={isDeleting}
          onClick={onDelete}
        >
          <Trash2 className="size-4 text-destructive" />
        </Button>
      </div>
    </div>
  );
}
