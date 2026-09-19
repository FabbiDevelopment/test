import { CheckCircle2, Circle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
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

  const handleBulkStatus = (completed: boolean) => {
    bulkUpdate.mutate(
      { todo_ids: selectedIds, completed },
      {
        onSuccess: () => {
          onClearSelection();
        },
      }
    );
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-foreground text-background px-4 py-2.5 rounded-full shadow-xl flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4 duration-200 border border-background/20">
      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-background/20 text-background">
        Đã chọn {selectedIds.length}
      </span>

      <div className="h-4 w-px bg-background/20" />

      <Button
        size="sm"
        variant="ghost"
        disabled={bulkUpdate.isPending}
        onClick={() => handleBulkStatus(true)}
        className="h-8 px-2.5 text-xs text-background hover:bg-background/20 hover:text-background gap-1.5"
      >
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
        <span>Đánh dấu hoàn thành</span>
      </Button>

      <Button
        size="sm"
        variant="ghost"
        disabled={bulkUpdate.isPending}
        onClick={() => handleBulkStatus(false)}
        className="h-8 px-2.5 text-xs text-background hover:bg-background/20 hover:text-background gap-1.5"
      >
        <Circle className="h-3.5 w-3.5 text-amber-400" />
        <span>Đánh dấu chưa làm</span>
      </Button>

      <div className="h-4 w-px bg-background/20" />

      <Button
        size="icon"
        variant="ghost"
        onClick={onClearSelection}
        className="h-7 w-7 rounded-full text-background/70 hover:bg-background/20 hover:text-background"
      >
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
