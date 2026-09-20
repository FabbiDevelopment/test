import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tag, useTags, useCreateTag, useDeleteTag } from "../api/tags";
import { Trash2, Tag as TagIcon, Plus } from "lucide-react";

const tagSchema = z.object({
  name: z.string().min(1, "Name is required").max(50, "Name too long"),
  color: z.string().optional(),
});

type TagFormData = z.infer<typeof tagSchema>;

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

const DEFAULT_COLORS = [
  "#ef4444", "#f97316", "#f59e0b", "#10b981", 
  "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"
];

export function TagManager({ open, onClose }: TagManagerProps) {
  const { data: tags = [] } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLORS[0]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: { name: "", color: DEFAULT_COLORS[0] },
  });

  const onSubmit = (data: TagFormData) => {
    createTag.mutate(
      { ...data, color: selectedColor },
      {
        onSuccess: () => {
          reset();
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5" />
            Manage Tags
          </DialogTitle>
        </DialogHeader>

        {/* Create Tag Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 border-b pb-4">
          <div className="space-y-1.5">
            <Label htmlFor="tag-name">Tag Name</Label>
            <div className="flex gap-2">
              <Input
                id="tag-name"
                placeholder="e.g. Work, Personal"
                {...register("name")}
              />
              <Button type="submit" size="sm" disabled={createTag.isPending}>
                <Plus className="h-4 w-4 mr-1" /> Add
              </Button>
            </div>
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Color</Label>
            <div className="flex gap-1.5">
              {DEFAULT_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`h-6 w-6 rounded-full border ${selectedColor === c ? "ring-2 ring-offset-2 ring-primary" : ""}`}
                  style={{ backgroundColor: c }}
                  onClick={() => setSelectedColor(c)}
                />
              ))}
            </div>
          </div>
        </form>

        {/* Tag List */}
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {tags.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-4">No tags created yet.</p>
          ) : (
            tags.map((tag) => (
              <div key={tag.id} className="flex items-center justify-between p-2 rounded-md border bg-card">
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: tag.color || "#6b7280" }}
                  />
                  <span className="text-sm font-medium">{tag.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive"
                  onClick={() => deleteTag.mutate(tag.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
