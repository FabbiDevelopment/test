import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useTags } from "../api/tags";
import { useAttachTagToTodo } from "../api/todos";
import type { Todo } from "../api/todos";

interface TagAttachModalProps {
  todo: Todo | null;
  onClose: () => void;
}

export function TagAttachModal({ todo, onClose }: TagAttachModalProps) {
  const { data: tags = [] } = useTags();
  const attachTag = useAttachTagToTodo();

  return (
    <Dialog open={!!todo} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Attach Tag to "{todo?.title}"</DialogTitle>
        </DialogHeader>
        <div className="flex flex-wrap gap-2 mt-4">
          {tags.map((tag) => (
            <Button
              key={tag.id}
              variant="outline"
              onClick={() => {
                if (todo) {
                  attachTag.mutate(
                    { todo_id: todo.id, tag_id: tag.id },
                    { onSuccess: onClose }
                  );
                }
              }}
              disabled={attachTag.isPending}
              style={{ borderColor: tag.color || "#ccc" }}
            >
              <div className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: tag.color || "#ccc" }} />
              {tag.name}
            </Button>
          ))}
          {tags.length === 0 && <p className="text-sm text-muted-foreground">No tags available. Manage tags to add some.</p>}
        </div>
      </DialogContent>
    </Dialog>
  );
}
