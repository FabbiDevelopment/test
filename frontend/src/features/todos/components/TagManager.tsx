import { useEffect } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useCreateTag, useDeleteTag, useTags, useUpdateTag } from "../api/todos";

const schema = z.object({ name: z.string().trim().min(1).max(50), color: z.string().regex(/^#[0-9a-fA-F]{6}$/) });
type FormData = z.infer<typeof schema>;

export function TagManager({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { data: tags = [] } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { name: "", color: "#64748b" } });
  useEffect(() => { if (!open) reset(); }, [open, reset]);

  return <Dialog open={open} onOpenChange={value => !value && onClose()}>
    <DialogContent>
      <DialogHeader><DialogTitle>Manage tags</DialogTitle></DialogHeader>
      <form className="flex gap-2" onSubmit={handleSubmit(data => createTag.mutate(data, { onSuccess: () => reset({ name: "", color: data.color }) }))}>
        <Input aria-label="Tag name" placeholder="New tag" {...register("name")} />
        <Input aria-label="Tag color" className="w-14 p-1" type="color" {...register("color")} />
        <Button type="submit" disabled={createTag.isPending}>Add</Button>
      </form>
      {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      <div className="divide-y">
        {tags.map(tag => <div key={tag.id} className="flex items-center gap-2 py-2">
          <span className="size-3 rounded-full" style={{ backgroundColor: tag.color || "#64748b" }} />
          <span className="flex-1 text-sm">{tag.name}</span>
          <Button variant="ghost" size="icon" title="Rename tag" onClick={() => { const name = window.prompt("Tag name", tag.name)?.trim(); if (name) updateTag.mutate({ id: tag.id, data: { name } }); }}><Pencil className="size-4" /></Button>
          <Button variant="ghost" size="icon" title="Delete tag" onClick={() => deleteTag.mutate(tag.id)}><Trash2 className="size-4" /></Button>
        </div>)}
        {!tags.length && <p className="py-6 text-center text-sm text-muted-foreground">No tags yet</p>}
      </div>
    </DialogContent>
  </Dialog>;
}