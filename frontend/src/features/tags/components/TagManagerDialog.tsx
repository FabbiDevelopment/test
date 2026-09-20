import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Plus, Trash2, Edit2, Check, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTag, useDeleteTag, useTags, useUpdateTag } from "../api/tags";
import type { Tag } from "../types/tag";
import { TagBadge } from "./TagBadge";

const PRESET_COLORS = [
  "#ef4444", // Red
  "#f97316", // Orange
  "#f59e0b", // Amber
  "#10b981", // Emerald
  "#06b6d4", // Cyan
  "#3b82f6", // Blue
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#64748b", // Slate
];

const HEX_COLOR_REGEX = /^#(?:[0-9a-fA-F]{3}){1,2}$/;

const tagSchema = z.object({
  name: z.string().trim().min(1, "Tag name is required").max(50, "Max 50 characters"),
  color: z
    .string()
    .regex(HEX_COLOR_REGEX, "Invalid hex color format (e.g. #3b82f6)")
    .optional()
    .or(z.literal("")),
});

type TagFormData = z.infer<typeof tagSchema>;

interface TagManagerDialogProps {
  open: boolean;
  onClose: () => void;
}

export function TagManagerDialog({ open, onClose }: TagManagerDialogProps) {
  const { data: tagData, isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[5]);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: { name: "", color: PRESET_COLORS[5] },
  });

  const onSubmit = (formData: TagFormData) => {
    createTag.mutate(
      { name: formData.name, color: selectedColor },
      {
        onSuccess: () => {
          reset();
        },
      }
    );
  };

  const startEdit = (tag: Tag) => {
    setEditingTag(tag);
    setEditName(tag.name);
    setEditColor(tag.color || PRESET_COLORS[5]);
  };

  const saveEdit = () => {
    if (!editingTag || !editName.trim()) return;
    if (editColor && !HEX_COLOR_REGEX.test(editColor)) return;
    updateTag.mutate(
      { id: editingTag.id, data: { name: editName.trim(), color: editColor } },
      {
        onSuccess: () => {
          setEditingTag(null);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>

        {/* Create new tag form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label htmlFor="tag-name">New Tag Name</Label>
            <div className="flex gap-2">
              <Input
                id="tag-name"
                placeholder="e.g. Work, Urgent, Bug..."
                {...register("name")}
                className="flex-1"
              />
              <Button type="submit" disabled={createTag.isPending} size="sm">
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          {/* Color palette */}
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Tag Color</Label>
            <div className="flex flex-wrap gap-2">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setSelectedColor(c)}
                  className={`w-6 h-6 rounded-full transition-transform ${
                    selectedColor === c ? "ring-2 ring-ring ring-offset-2 scale-110" : ""
                  }`}
                  style={{ backgroundColor: c }}
                  title={c}
                />
              ))}
            </div>
          </div>
        </form>

        <div className="border-t my-4" />

        {/* Existing tags list */}
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          <Label className="text-xs text-muted-foreground">Existing Tags</Label>
          {isLoading && <p className="text-sm text-muted-foreground">Loading tags...</p>}

          {tagData && tagData.items.length === 0 && (
            <p className="text-sm text-muted-foreground italic py-2">
              No tags created yet. Create one above!
            </p>
          )}

          {tagData &&
            tagData.items.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 rounded-md bg-muted/30 hover:bg-muted/60 transition-colors"
              >
                {editingTag?.id === tag.id ? (
                  <div className="flex items-center gap-2 flex-1 mr-2">
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="h-8 text-sm"
                      autoFocus
                    />
                    <div className="flex gap-1">
                      {PRESET_COLORS.slice(0, 5).map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setEditColor(c)}
                          className={`w-4 h-4 rounded-full ${
                            editColor === c ? "ring-2 ring-ring" : ""
                          }`}
                          style={{ backgroundColor: c }}
                        />
                      ))}
                    </div>
                    <Button size="icon" variant="ghost" className="h-7 w-7" onClick={saveEdit}>
                      <Check className="h-4 w-4 text-emerald-600" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7"
                      onClick={() => setEditingTag(null)}
                    >
                      <X className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <TagBadge tag={tag} size="md" />
                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={() => startEdit(tag)}
                        title="Edit Tag"
                      >
                        <Edit2 className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => deleteTag.mutate(tag.id)}
                        disabled={deleteTag.isPending}
                        title="Delete Tag"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
