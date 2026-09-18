import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from "../api/todos";
import type { Tag } from "../api/todos";
import { tagSchema, type TagFormData } from "../schemas/tag";

export function TagManager({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { data: tags = [], isLoading, error } = useTags();
  const create = useCreateTag(), update = useUpdateTag(), remove = useDeleteTag();
  const [editing, setEditing] = useState<Tag | null>(null);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema), defaultValues: { name: "", color: "#336699" },
  });
  const clear = () => { setEditing(null); reset({ name: "", color: "#336699" }); };
  const submit = (data: TagFormData) => {
    if (editing) update.mutate({ id: editing.id, data }, { onSuccess: clear });
    else create.mutate(data, { onSuccess: clear });
  };
  const pending = create.isPending || update.isPending || remove.isPending;
  return (
    <Dialog open={open} onOpenChange={(value) => { if (!value) { clear(); onClose(); } }}>
      <DialogContent>
        <DialogHeader><DialogTitle>Manage Tags</DialogTitle>
          <DialogDescription>Create, rename or delete your tags.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(submit)} className="space-y-3">
          <Label htmlFor="tag-name">Tag name</Label>
          <Input id="tag-name" {...register("name")} aria-invalid={!!errors.name} />
          {errors.name && <p role="alert" className="text-sm text-destructive">{errors.name.message}</p>}
          <Label htmlFor="tag-color">Tag color</Label>
          <Input id="tag-color" type="color" {...register("color")} />
          {errors.color && <p role="alert">{errors.color.message}</p>}
          <div className="flex gap-2">
            <Button type="submit" disabled={pending}>{editing ? "Save tag" : "Create tag"}</Button>
            {editing && <Button type="button" variant="outline" onClick={clear}>Cancel edit</Button>}
          </div>
        </form>
        {isLoading && <p>Loading tags...</p>}
        {error && <p role="alert">Failed to load tags.</p>}
        <ul className="space-y-2 max-h-64 overflow-auto">
          {tags.map((tag) => <li key={tag.id} className="flex gap-2 items-center" data-testid="tag-row">
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: tag.color ?? "#336699" }} />
            <span className="flex-1">{tag.name}</span>
            <Button variant="outline" size="sm" disabled={pending} aria-label={`Edit tag ${tag.name}`}
              onClick={() => { setEditing(tag); reset({ name: tag.name, color: tag.color ?? "#336699" }); }}>Edit</Button>
            <Button variant="outline" size="sm" disabled={pending} aria-label={`Delete tag ${tag.name}`}
              onClick={() => remove.mutate(tag.id, { onSuccess: () => { if (editing?.id === tag.id) clear(); } })}>Delete</Button>
          </li>)}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
