import React, { useState } from "react";
import { Tag as TagIcon, Plus, Trash2, Edit2, Check, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useTags,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  type Tag,
} from "../api/tags";

interface TagManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const COLOR_OPTIONS = [
  "#3b82f6", // Blue
  "#ef4444", // Red
  "#10b981", // Green
  "#f59e0b", // Yellow
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#6b7280", // Gray
];

export const TagManagerModal: React.FC<TagManagerModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { data: tags = [], isLoading } = useTags();
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3b82f6");

  const [editingTagId, setEditingTagId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [editingColor, setEditingColor] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    createTagMutation.mutate(
      { name: newTagName.trim(), color: newTagColor },
      {
        onSuccess: () => {
          setNewTagName("");
        },
      }
    );
  };

  const handleStartEdit = (tag: Tag) => {
    setEditingTagId(tag.id);
    setEditingName(tag.name);
    setEditingColor(tag.color || "#3b82f6");
  };

  const handleSaveEdit = (tagId: string) => {
    if (!editingName.trim()) return;
    updateTagMutation.mutate(
      {
        id: tagId,
        data: { name: editingName.trim(), color: editingColor },
      },
      {
        onSuccess: () => {
          setEditingTagId(null);
        },
      }
    );
  };

  const handleDelete = (tagId: string) => {
    if (confirm("Are you sure you want to delete this tag?")) {
      deleteTagMutation.mutate(tagId);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5" />
            Manage Tags
          </DialogTitle>
        </DialogHeader>

        {/* Create Tag Form */}
        <form onSubmit={handleCreate} className="space-y-3 pt-2">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Enter tag name (e.g. Work, Urgent)..."
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={!newTagName.trim() || createTagMutation.isPending}
              className="gap-1"
            >
              <Plus className="h-4 w-4" />
              Add
            </Button>
          </div>

          {/* Color Picker */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Color:</span>
            <div className="flex items-center gap-1.5">
              {COLOR_OPTIONS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setNewTagColor(c)}
                  style={{ backgroundColor: c }}
                  className={`h-5 w-5 rounded-full transition-transform ${
                    newTagColor === c ? "ring-2 ring-offset-2 ring-primary scale-110" : ""
                  }`}
                />
              ))}
            </div>
          </div>
        </form>

        <div className="border-t my-4" />

        {/* Tag List */}
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {isLoading ? (
            <p className="text-xs text-muted-foreground text-center py-4">Loading tags...</p>
          ) : tags.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">
              No tags created yet. Add one above!
            </p>
          ) : (
            tags.map((tag: Tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 rounded-md border bg-card text-sm"
              >
                {editingTagId === tag.id ? (
                  <div className="flex items-center gap-2 flex-1 mr-2">
                    <Input
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      className="h-8 text-xs flex-1"
                    />
                    <div className="flex items-center gap-1">
                      {COLOR_OPTIONS.map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setEditingColor(c)}
                          style={{ backgroundColor: c }}
                          className={`h-4 w-4 rounded-full ${
                            editingColor === c ? "ring-2 ring-offset-1 ring-primary" : ""
                          }`}
                        />
                      ))}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleSaveEdit(tag.id)}
                      className="h-8 w-8 p-0"
                    >
                      <Check className="h-4 w-4 text-green-600" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingTagId(null)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: tag.color || "#3b82f6" }}
                      />
                      <span className="font-medium">{tag.name}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleStartEdit(tag)}
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(tag.id)}
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
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
};
