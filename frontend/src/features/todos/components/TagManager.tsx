import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type Tag, useCreateTag, useDeleteTag, useUpdateTag } from "../api/todos";
import { tagSchema, type TagFormData } from "../schemas/tag";

export function TagManager({ tags }: { tags: Tag[] }) {
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const { register, handleSubmit, reset, formState: { errors } } =
    useForm<TagFormData>({ resolver: zodResolver(tagSchema) });

  const submit = (data: TagFormData) =>
    createTag.mutate(data, { onSuccess: () => reset() });

  return (
    <section className="mb-6 rounded-lg border p-4" aria-labelledby="tag-manager-title">
      <h2 id="tag-manager-title" className="font-semibold mb-3">Manage tags</h2>
      <form onSubmit={handleSubmit(submit)} className="grid gap-2 sm:grid-cols-[1fr_140px_auto]">
        <div>
          <Label htmlFor="tag-name" className="sr-only">Tag name</Label>
          <Input id="tag-name" placeholder="Tag name" {...register("name")} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <Input aria-label="Tag color" placeholder="#2563eb" {...register("color")} />
        <Button type="submit" disabled={createTag.isPending}>Add tag</Button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {tags.map((tag) => editingId === tag.id ? (
          <div key={tag.id} className="flex gap-1">
            <Input value={editingName} onChange={(event) => setEditingName(event.target.value)} />
            <Button size="sm" onClick={() => updateTag.mutate(
              { id: tag.id, data: { name: editingName } },
              { onSuccess: () => setEditingId(null) }
            )}>Save</Button>
          </div>
        ) : (
          <div key={tag.id} className="flex items-center gap-1 rounded-full border px-2 py-1 text-xs">
            <span style={{ color: tag.color || undefined }}>{tag.name}</span>
            <button type="button" aria-label={`Rename ${tag.name}`} onClick={() => {
              setEditingId(tag.id);
              setEditingName(tag.name);
            }}>✎</button>
            <button type="button" aria-label={`Delete ${tag.name}`} onClick={() => deleteTag.mutate(tag.id)}>×</button>
          </div>
        ))}
      </div>
    </section>
  );
}
