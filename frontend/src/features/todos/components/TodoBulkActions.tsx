import { CheckCheck, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBulkUpdateTodoStatus } from "../api/todos";

interface TodoBulkActionsProps {
  selectedTodoIds: string[];
  userId: string;
  onComplete: () => void;
}

export function TodoBulkActions({
  selectedTodoIds,
  userId,
  onComplete,
}: TodoBulkActionsProps) {
  const bulkUpdate = useBulkUpdateTodoStatus();
  const selectedCount = selectedTodoIds.length;

  if (selectedCount === 0) {
    return null;
  }

  const updateStatus = (completed: boolean) => {
    bulkUpdate.mutate(
      { todoIds: selectedTodoIds, completed, userId },
      { onSuccess: onComplete },
    );
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2.5">
      <p className="text-sm font-medium">
        {selectedCount} todo{selectedCount === 1 ? "" : "s"} selected
      </p>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={bulkUpdate.isPending}
          onClick={() => updateStatus(false)}
        >
          <RotateCcw className="h-4 w-4" />
          Mark active
        </Button>
        <Button
          type="button"
          size="sm"
          disabled={bulkUpdate.isPending}
          onClick={() => updateStatus(true)}
        >
          <CheckCheck className="h-4 w-4" />
          Mark completed
        </Button>
      </div>
    </div>
  );
}
