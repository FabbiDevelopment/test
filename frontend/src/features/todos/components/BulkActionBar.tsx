import { CheckCircle2, Circle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useBulkUpdateStatus } from "../api/todos";

interface BulkActionBarProps {
  selectedIds: string[];
  onClearSelection: () => void;
}

export function BulkActionBar({
  selectedIds,
  onClearSelection,
}: BulkActionBarProps) {
  const bulkUpdate = useBulkUpdateStatus();

  if (selectedIds.length === 0) return null;

  const handleBulkStatus = async (completed: boolean) => {
    await bulkUpdate.mutateAsync({
      todo_ids: selectedIds,
      completed,
    });
    onClearSelection();
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg px-4 animate-in fade-in slide-in-from-bottom-4 duration-200">
      <Card className="p-3 shadow-lg border-primary/20 bg-background/95 backdrop-blur flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="bg-primary/10 text-primary font-semibold text-xs px-2.5 py-1 rounded-full">
            {selectedIds.length}
          </span>
          <span className="text-sm font-medium">selected</span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="default"
            className="h-8 text-xs gap-1.5"
            onClick={() => handleBulkStatus(true)}
            disabled={bulkUpdate.isPending}
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Complete All
          </Button>

          <Button
            size="sm"
            variant="outline"
            className="h-8 text-xs gap-1.5"
            onClick={() => handleBulkStatus(false)}
            disabled={bulkUpdate.isPending}
          >
            <Circle className="h-3.5 w-3.5" />
            Active All
          </Button>

          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={onClearSelection}
            disabled={bulkUpdate.isPending}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>
  );
}
