import { useState } from "react";
import { Tag as TagIcon, Plus, Trash2, Pencil, Check, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  useTags,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  type Tag,
} from "../api/tagsApi";

interface TagManagerModalProps {
  open: boolean;
  onClose: () => void;
}

const COLOR_PRESETS = [
  "#3B82F6", // Blue
  "#EF4444", // Red
  "#10B981", // Green
  "#8B5CF6", // Purple
  "#F59E0B", // Yellow
  "#EC4899", // Pink
  "#6B7280", // Gray
];

export function TagManagerModal({ open, onClose }: TagManagerModalProps) {
  const { data: tags = [], isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [name, setName] = useState("");
  const [selectedColor, setSelectedColor] = useState(COLOR_PRESETS[0]);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createTag.mutate(
      { name: name.trim(), color: selectedColor },
      {
        onSuccess: () => {
          setName("");
        },
      }
    );
  };

  const handleStartEdit = (tag: Tag) => {
    setEditingTag(tag);
    setEditName(tag.name);
    setEditColor(tag.color || COLOR_PRESETS[0]);
  };

  const handleSaveEdit = () => {
    if (!editingTag || !editName.trim()) return;
    updateTag.mutate(
      {
        id: editingTag.id,
        data: { name: editName.trim(), color: editColor },
      },
      {
        onSuccess: () => {
          setEditingTag(null);
        },
      }
    );
  };

  const handleDelete = (id: string) => {
    deleteTag.mutate(id);
  };

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-semibold">
            <TagIcon className="h-4 w-4 text-primary" />
            Quản lý thẻ phân loại (Tags)
          </DialogTitle>
        </DialogHeader>

        {/* Create Tag Form */}
        <form onSubmit={handleCreate} className="space-y-3 pt-2">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Tên thẻ mới (ví dụ: Work, Personal)..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="text-xs h-9"
              maxLength={50}
            />
            <Button
              type="submit"
              size="sm"
              disabled={!name.trim() || createTag.isPending}
              className="h-9 px-3 gap-1"
            >
              <Plus className="h-4 w-4" />
              <span>Tạo</span>
            </Button>
          </div>

          <div className="flex items-center gap-1.5 pt-1">
            <span className="text-xs text-muted-foreground mr-1">Màu đại diện:</span>
            {COLOR_PRESETS.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => setSelectedColor(color)}
                className={`h-5 w-5 rounded-full transition-transform ${selectedColor === color ? "ring-2 ring-offset-2 ring-primary scale-110" : ""
                  }`}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </form>

        <div className="my-2 border-t" />

        <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
          {isLoading && (
            <p className="text-xs text-center text-muted-foreground py-4">
              Đang tải danh sách thẻ...
            </p>
          )}

          {!isLoading && tags.length === 0 && (
            <p className="text-xs text-center text-muted-foreground py-4">
              Chưa có thẻ tag nào. Hãy tạo thẻ đầu tiên!
            </p>
          )}

          {tags.map((tag) => {
            const isEditing = editingTag?.id === tag.id;

            if (isEditing) {
              return (
                <div
                  key={tag.id}
                  className="flex items-center gap-2 p-2 rounded-lg border bg-accent/40"
                >
                  <Input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="h-7 text-xs flex-1"
                  />
                  <div className="flex gap-1">
                    {COLOR_PRESETS.map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setEditColor(c)}
                        className={`h-4 w-4 rounded-full ${editColor === c ? "ring-1 ring-offset-1 ring-primary" : ""
                          }`}
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7 text-emerald-600"
                    onClick={handleSaveEdit}
                  >
                    <Check className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7 text-muted-foreground"
                    onClick={() => setEditingTag(null)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              );
            }

            return (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 rounded-lg border bg-card hover:bg-accent/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: tag.color || "#3B82F6" }}
                  />
                  <span className="text-xs font-medium">{tag.name}</span>
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    onClick={() => handleStartEdit(tag)}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(tag.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
