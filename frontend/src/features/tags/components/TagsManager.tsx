import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useTags, useCreateTag, useDeleteTag } from "../api/tags";

interface TagsManagerProps {
  open: boolean;
  onClose: () => void;
}

export function TagsManager({ open, onClose }: TagsManagerProps) {
  const { data: tags, isLoading } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3b82f6");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    createTag.mutate(
      { name: newTagName.trim(), color: newTagColor },
      { onSuccess: () => setNewTagName("") }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleCreate} className="flex gap-2 items-center mt-4">
          <Input 
            value={newTagName} 
            onChange={(e) => setNewTagName(e.target.value)} 
            placeholder="New tag name" 
            className="flex-1"
          />
          <Input 
            type="color" 
            value={newTagColor} 
            onChange={(e) => setNewTagColor(e.target.value)} 
            className="w-12 p-1 h-10"
          />
          <Button type="submit" disabled={createTag.isPending || !newTagName.trim()}>
            Add
          </Button>
        </form>

        <div className="mt-4 space-y-2 max-h-[60vh] overflow-y-auto">
          {isLoading ? (
            <div className="text-center text-muted-foreground text-sm py-4">Loading tags...</div>
          ) : tags?.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-4">No tags created yet.</div>
          ) : (
            tags?.map((tag) => (
              <div key={tag.id} className="flex items-center justify-between p-2 border rounded-md">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: tag.color || "#ccc" }} 
                  />
                  <span className="text-sm font-medium">{tag.name}</span>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-destructive h-8 px-2"
                  onClick={() => deleteTag.mutate(tag.id)}
                  disabled={deleteTag.isPending}
                >
                  Delete
                </Button>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
