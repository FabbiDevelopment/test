import { useState } from "react";
import { Tag as TagIcon, Plus, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useTags, useCreateTag, useDeleteTag } from "../api/tags";

const PRESET_COLORS = [
  "#ef4444", // Red
  "#f97316", // Orange
  "#eab308", // Yellow
  "#10b981", // Emerald
  "#06b6d4", // Cyan
  "#3b82f6", // Blue
  "#6366f1", // Indigo
  "#a855f7", // Purple
  "#ec4899", // Pink
  "#64748b", // Slate
];

interface TagManagerDialogProps {
  open: boolean;
  onClose: () => void;
}

export function TagManagerDialog({ open, onClose }: TagManagerDialogProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();

  const [tagName, setTagName] = useState("");
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[6]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagName.trim()) return;

    await createTag.mutateAsync({
      name: tagName.trim(),
      color: selectedColor,
    });
    setTagName("");
  };

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this tag?")) {
      await deleteTag.mutateAsync(id);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5 text-primary" />
            Manage Tags
          </DialogTitle>
        </DialogHeader>

        {/* Create new tag form */}
        <form onSubmit={handleCreate} className="space-y-3 pt-2">
          <div className="flex gap-2">
            <Input
              placeholder="New tag name..."
              value={tagName}
              onChange={(e) => setTagName(e.target.value)}
              className="flex-1"
              maxLength={50}
            />
            <Button
              type="submit"
              size="sm"
              disabled={!tagName.trim() || createTag.isPending}
            >
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>

          {/* Color Presets */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-muted-foreground font-medium">Color:</span>
            {PRESET_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                className={`w-6 h-6 rounded-full transition-transform ${
                  selectedColor === color
                    ? "ring-2 ring-offset-2 ring-primary scale-110"
                    : "hover:scale-105"
                }`}
                style={{ backgroundColor: color }}
                onClick={() => setSelectedColor(color)}
              />
            ))}
          </div>
        </form>

        <Separator className="my-2" />

        {/* Tag list */}
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="text-center py-6 text-sm text-muted-foreground">
              Loading tags...
            </div>
          ) : tags.length === 0 ? (
            <div className="text-center py-6 text-sm text-muted-foreground">
              No tags created yet.
            </div>
          ) : (
            tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 rounded-md border bg-card text-sm"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-3.5 h-3.5 rounded-full"
                    style={{ backgroundColor: tag.color || "#6366f1" }}
                  />
                  <span className="font-medium">{tag.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive hover:text-destructive"
                  onClick={() => handleDelete(tag.id)}
                  disabled={deleteTag.isPending}
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
