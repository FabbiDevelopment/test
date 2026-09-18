import { CheckCircle2, Circle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBulkUpdateStatus } from "../api/todos";

interface BulkActionsBarProps {
  selectedIds: string[];
  onClear: () => void;
}

export function BulkActionsBar({ selectedIds, onClear }: BulkActionsBarProps) {
  const bulkUpdate = useBulkUpdateStatus();

  if (selectedIds.length === 0) return null;

  const run = (completed: boolean) => {
    bulkUpdate.mutate(
      { todoIds: selectedIds, completed },
      { onSuccess: onClear }
    );
  };

  return (
    <div
      className="flex items-center justify-between rounded-lg border bg-accent/40 px-3 py-2 mb-2"
      data-testid="bulk-actions-bar"
    >
      <span className="text-sm font-medium">
        {selectedIds.length} selected
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={bulkUpdate.isPending}
          onClick={() => run(true)}
        >
          <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
          Mark complete
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={bulkUpdate.isPending}
          onClick={() => run(false)}
        >
          <Circle className="h-3.5 w-3.5 mr-1" />
          Mark active
        </Button>
        <Button variant="ghost" size="sm" onClick={onClear}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
