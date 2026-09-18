import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Tag } from "../api/todos";
import { useCreateTag, useDeleteTag, useUpdateTag } from "../api/tags";

const tagSchema = z.object({ name: z.string().trim().min(1, "Enter a tag name").max(50, "Maximum 50 characters") });
type TagForm = z.infer<typeof tagSchema>;

export function TagManager({ tags }: { tags: Tag[] }) {
  const create = useCreateTag(); const update = useUpdateTag(); const remove = useDeleteTag();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<TagForm>({ resolver: zodResolver(tagSchema), defaultValues: { name: "" } });
  return <details className="mb-4 rounded border p-3"><summary className="cursor-pointer font-medium text-sm">Manage tags</summary><form className="flex gap-2 mt-3" onSubmit={handleSubmit((data) => create.mutate(data, { onSuccess: () => reset() }))}><div className="flex-1"><Input aria-label="New tag name" {...register("name")} placeholder="New tag name" maxLength={50} />{errors.name && <p className="text-xs text-destructive mt-1">{errors.name.message}</p>}</div><Button size="sm" disabled={create.isPending}>Add</Button></form><div className="mt-3 space-y-2">{tags.map((tag) => <div key={tag.id} className="flex justify-between text-sm"><span>{tag.name}</span><span className="flex gap-2"><button type="button" className="underline" onClick={() => { const next = window.prompt("New tag name", tag.name); if (next?.trim()) update.mutate({ id: tag.id, name: next.trim(), color: tag.color || undefined }); }}>Rename</button><button type="button" className="text-destructive underline" onClick={() => remove.mutate(tag.id)}>Delete</button></span></div>)}</div></details>;
}
