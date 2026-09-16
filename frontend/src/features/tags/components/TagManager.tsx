import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Trash2, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { useTags, useCreateTag, useUpdateTag, useDeleteTag, type Tag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";
import { TagBadge } from "./TagBadge";

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

const PREDEFINED_COLORS = [
  "#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e",
  "#06b6d4", "#3b82f6", "#6366f1", "#a855f7", "#ec4899",
];

export function TagManager({ open, onClose }: TagManagerProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [editingTag, setEditingTag] = useState<Tag | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: {
      name: "",
      color: PREDEFINED_COLORS[0],
    },
  });

  const watchColor = watch("color");

  useEffect(() => {
    if (editingTag) {
      setValue("name", editingTag.name);
      setValue("color", editingTag.color || PREDEFINED_COLORS[0]);
    } else {
      reset({ name: "", color: PREDEFINED_COLORS[0] });
    }
  }, [editingTag, setValue, reset]);

  const onSubmit = (data: TagFormData) => {
    if (editingTag) {
      updateTag.mutate(
        { id: editingTag.id, data },
        {
          onSuccess: () => {
            setEditingTag(null);
            reset();
          },
        }
      );
    } else {
      createTag.mutate(data, {
        onSuccess: () => {
          reset();
        },
      });
    }
  };

  const isPending = createTag.isPending || updateTag.isPending;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) {
        setEditingTag(null);
        reset();
        onClose();
      }
    }}>
      <DialogContent className="sm:max-w-md max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">{editingTag ? "Edit Tag" : "New Tag"}</Label>
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  id="name"
                  placeholder="Tag name"
                  {...register("name")}
                />
              </div>
              <Input
                type="color"
                className="w-12 h-10 p-1 cursor-pointer"
                {...register("color")}
              />
              <Button type="submit" disabled={isPending}>
                {editingTag ? "Save" : <Plus className="h-4 w-4" />}
              </Button>
              {editingTag && (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setEditingTag(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>
          <div className="flex gap-1 flex-wrap">
            {PREDEFINED_COLORS.map(c => (
              <button
                key={c}
                type="button"
                className={`w-6 h-6 rounded-full border-2 ${watchColor === c ? 'border-primary' : 'border-transparent'}`}
                style={{ backgroundColor: c }}
                onClick={() => setValue("color", c)}
              />
            ))}
          </div>
        </form>

        <Separator className="my-4" />

        <div className="space-y-3">
          <Label>Existing Tags</Label>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading tags...</p>
          ) : tags.length === 0 ? (
            <p className="text-sm text-muted-foreground">No tags created yet.</p>
          ) : (
            <ul className="space-y-2">
              {tags.map((tag) => (
                <li key={tag.id} className="flex items-center justify-between p-2 rounded-md border bg-card">
                  <TagBadge tag={tag} />
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setEditingTag(tag)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={() => {
                        if (confirm("Are you sure you want to delete this tag?")) {
                          deleteTag.mutate(tag.id);
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
