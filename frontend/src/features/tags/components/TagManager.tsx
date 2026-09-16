import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateTag,
  useDeleteTag,
  useTags,
  useUpdateTag,
  type Tag,
} from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";

/** THÊM: Tag management UI — list/create/rename/delete với react-hook-form + zod (Level 4) */
export function TagManager() {
  const { data: tags = [] } = useTags();
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
    defaultValues: { name: "", color: "" },
  });

  const onCreate = (data: TagFormData) => {
    createTag.mutate(
      { name: data.name, color: data.color || undefined },
      { onSuccess: () => reset() }
    );
  };

  const handleRename = (tag: Tag) => {
    const next = window.prompt("Rename tag", tag.name);
    if (!next || next === tag.name) return;
    updateTag.mutate({ id: tag.id, data: { name: next } });
  };

  return (
    <div className="space-y-4 p-4 rounded-lg border bg-muted/20">
      <h3 className="font-semibold text-sm">Manage Tags</h3>

      <form onSubmit={handleSubmit(onCreate)} className="flex flex-wrap gap-2 items-end">
        <div className="space-y-1 flex-1 min-w-[140px]">
          <Label htmlFor="tag-name">New tag</Label>
          <Input id="tag-name" placeholder="e.g. Work" {...register("name")} />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>
        <div className="space-y-1 w-28">
          <Label htmlFor="tag-color">Color</Label>
          <Input id="tag-color" placeholder="#3b82f6" {...register("color")} />
        </div>
        <Button type="submit" size="sm" disabled={createTag.isPending}>
          Add Tag
        </Button>
      </form>

      <ul className="space-y-1">
        {tags.map((tag) => (
          <li
            key={tag.id}
            className="flex items-center justify-between text-sm py-1 px-2 rounded hover:bg-accent/50"
          >
            <span style={{ color: tag.color ?? undefined }}>{tag.name}</span>
            <div className="flex gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleRename(tag)}
              >
                Rename
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="text-destructive"
                onClick={() => deleteTag.mutate(tag.id)}
              >
                Delete
              </Button>
            </div>
          </li>
        ))}
        {tags.length === 0 && (
          <p className="text-xs text-muted-foreground">No tags yet.</p>
        )}
      </ul>
    </div>
  );
}
