import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Trash2 } from "lucide-react";
import { useTags, useCreateTag, useDeleteTag } from "../api/tags";

interface TagManagementModalProps {
  open: boolean;
  onClose: () => void;
}

export function TagManagementModal({ open, onClose }: TagManagementModalProps) {
  const { data: tags = [] } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();
  
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3b82f6");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    createTag.mutate({ name: newTagName, color: newTagColor }, {
      onSuccess: () => {
        setNewTagName("");
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleCreate} className="flex items-center gap-2 mb-4">
          <Input 
            type="color" 
            value={newTagColor}
            onChange={(e) => setNewTagColor(e.target.value)}
            className="w-12 h-10 p-1 cursor-pointer"
          />
          <Input 
            placeholder="New tag name"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" disabled={createTag.isPending}>Add</Button>
        </form>

        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {tags.map((tag) => (
            <div key={tag.id} className="flex items-center justify-between p-2 border rounded-md">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tag.color || "#ccc" }} />
                <span>{tag.name}</span>
              </div>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => deleteTag.mutate(tag.id)}
                disabled={deleteTag.isPending}
                className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 w-8"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          {tags.length === 0 && <p className="text-center text-sm text-muted-foreground">No tags found.</p>}
        </div>
      </DialogContent>
    </Dialog>
  );
}
