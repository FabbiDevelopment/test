import { useState } from "react";
import { Plus, Pencil, Trash2, Tag as TagIcon, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { tagSchema, type TagFormData } from "../schemas/tag";
import { useTags, useCreateTag, useUpdateTag, useDeleteTag, type Tag } from "../api/tags";

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

export function TagManager({ open, onClose }: TagManagerProps) {
  const { data: tags, isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [editingTag, setEditingTag] = useState<Tag | null>(null);

  const form = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: { name: "", color: "#000000" },
  });

  const onSubmit = (data: TagFormData) => {
    if (editingTag) {
      updateTag.mutate(
        { id: editingTag.id, data },
        {
          onSuccess: () => {
            setEditingTag(null);
            form.reset({ name: "", color: "#000000" });
          },
        }
      );
    } else {
      createTag.mutate(data, {
        onSuccess: () => {
          form.reset({ name: "", color: "#000000" });
        },
      });
    }
  };

  const handleEdit = (tag: Tag) => {
    setEditingTag(tag);
    form.reset({ name: tag.name, color: tag.color || "#000000" });
  };

  const handleCancelEdit = () => {
    setEditingTag(null);
    form.reset({ name: "", color: "#000000" });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="w-5 h-5" /> Manage Tags
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <form onSubmit={form.handleSubmit(onSubmit)} className="flex gap-2 items-start">
            <div className="flex-1 space-y-1">
              <Input
                placeholder="Tag name..."
                {...form.register("name")}
              />
              {form.formState.errors.name && (
                <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
              )}
            </div>
            <Input
              type="color"
              className="w-12 h-10 p-1 cursor-pointer"
              {...form.register("color")}
            />
            {editingTag ? (
              <>
                <Button type="submit" disabled={updateTag.isPending}>
                  Save
                </Button>
                <Button type="button" variant="ghost" onClick={handleCancelEdit}>
                  <X className="w-4 h-4" />
                </Button>
              </>
            ) : (
              <Button type="submit" disabled={createTag.isPending}>
                <Plus className="w-4 h-4" />
              </Button>
            )}
          </form>

          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {isLoading ? (
              <p className="text-center text-sm text-muted-foreground py-4">Loading tags...</p>
            ) : tags?.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-4">No tags yet.</p>
            ) : (
              tags?.map((tag) => (
                <div key={tag.id} className="flex items-center justify-between p-2 rounded border bg-card">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tag.color || "#ccc" }}
                    />
                    <span className="text-sm font-medium">{tag.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => handleEdit(tag)}
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      onClick={() => deleteTag.mutate(tag.id)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
