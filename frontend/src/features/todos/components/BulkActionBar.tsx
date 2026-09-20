import React from "react";
import { CheckCircle2, Circle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBulkUpdateStatus } from "../api/tags";

interface BulkActionBarProps {
  selectedIds: string[];
  onClearSelection: () => void;
}

export const BulkActionBar: React.FC<BulkActionBarProps> = ({
  selectedIds,
  onClearSelection,
}) => {
  const bulkUpdateMutation = useBulkUpdateStatus();

  if (selectedIds.length === 0) return null;

  const handleSetCompleted = (completed: boolean) => {
    bulkUpdateMutation.mutate(
      { todo_ids: selectedIds, completed },
      {
        onSuccess: () => {
          onClearSelection();
        },
      }
    );
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-popover text-popover-foreground border shadow-xl rounded-full px-6 py-3 flex items-center gap-4 animate-in slide-in-from-bottom-5">
      <span className="text-sm font-medium">
        <span className="bg-primary text-primary-foreground font-bold px-2 py-0.5 rounded-full text-xs mr-1">
          {selectedIds.length}
        </span>
        items selected
      </span>

      <div className="h-4 w-px bg-border" />

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="secondary"
          disabled={bulkUpdateMutation.isPending}
          onClick={() => handleSetCompleted(true)}
          className="gap-1 text-xs"
        >
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          Mark Completed
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={bulkUpdateMutation.isPending}
          onClick={() => handleSetCompleted(false)}
          className="gap-1 text-xs"
        >
          <Circle className="h-3.5 w-3.5 text-yellow-600" />
          Mark Active
        </Button>
      </div>

      <Button
        size="sm"
        variant="ghost"
        onClick={onClearSelection}
        className="h-7 w-7 p-0 rounded-full"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
};
