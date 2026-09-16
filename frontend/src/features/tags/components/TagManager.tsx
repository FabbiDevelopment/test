import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Pencil, Trash2, Check, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useTags,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  type Tag,
} from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tagSchema";

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

const PRESET_COLORS = [
  "#EF4444", // Red
  "#F59E0B", // Amber
  "#10B981", // Emerald
  "#3B82F6", // Blue
  "#8B5CF6", // Purple
  "#EC4899", // Pink
  "#64748B", // Slate
];

export function TagManager({ open, onClose }: TagManagerProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [editingTagId, setEditingTagId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("#3B82F6");
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[3]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: {
      name: "",
      color: PRESET_COLORS[3],
    },
  });

  const handleCreate = (data: TagFormData) => {
    createTag.mutate(
      { name: data.name, color: selectedColor },
      {
        onSuccess: () => {
          reset();
        },
      }
    );
  };

  const startEdit = (tag: Tag) => {
    setEditingTagId(tag.id);
    setEditName(tag.name);
    setEditColor(tag.color || "#3B82F6");
  };

  const handleSaveEdit = (tagId: string) => {
    if (!editName.trim()) return;
    updateTag.mutate(
      { id: tagId, data: { name: editName.trim(), color: editColor } },
      {
        onSuccess: () => {
          setEditingTagId(null);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>

        {/* Create new tag form */}
        <form onSubmit={handleSubmit(handleCreate)} className="space-y-3 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="tag-name">New Tag Name</Label>
            <div className="flex gap-2">
              <Input
                id="tag-name"
                placeholder="e.g. Work, Urgent, Bug"
                {...register("name")}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={createTag.isPending}
                size="sm"
                className="shrink-0"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Color</Label>
            <div className="flex items-center gap-2">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setSelectedColor(c)}
                  className={`h-6 w-6 rounded-full transition-transform ${
                    selectedColor === c ? "ring-2 ring-offset-2 ring-primary scale-110" : ""
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>
        </form>

        <div className="border-t my-3" />

        {/* Existing tags list */}
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Existing Tags ({tags.length})
          </Label>

          {isLoading ? (
            <p className="text-sm text-muted-foreground py-4 text-center">Loading tags...</p>
          ) : tags.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No tags created yet.
            </p>
          ) : (
            tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 rounded-md border bg-card hover:bg-accent/40 transition-colors gap-2"
              >
                {editingTagId === tag.id ? (
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      type="color"
                      value={editColor}
                      onChange={(e) => setEditColor(e.target.value)}
                      className="h-6 w-6 rounded border cursor-pointer p-0"
                    />
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="h-7 text-xs flex-1"
                      autoFocus
                    />
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-primary"
                      onClick={() => handleSaveEdit(tag.id)}
                      disabled={updateTag.isPending}
                    >
                      <Check className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7"
                      onClick={() => setEditingTagId(null)}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <span
                        className="h-3 w-3 rounded-full shrink-0"
                        style={{ backgroundColor: tag.color || "#3B82F6" }}
                      />
                      <span className="text-sm font-medium">{tag.name}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-muted-foreground hover:text-foreground"
                        onClick={() => startEdit(tag)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => deleteTag.mutate(tag.id)}
                        disabled={deleteTag.isPending}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
