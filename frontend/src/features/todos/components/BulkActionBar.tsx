import { CheckCircle2, Circle, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBulkDeleteTodos, useBulkUpdateStatus } from "../api/todos";

interface BulkActionBarProps {
  selectedIds: string[];
  onClearSelection: () => void;
}

export function BulkActionBar({
  selectedIds,
  onClearSelection,
}: BulkActionBarProps) {
  const bulkUpdate = useBulkUpdateStatus();
  const bulkDelete = useBulkDeleteTodos();
  const count = selectedIds.length;
  const isBusy = bulkUpdate.isPending || bulkDelete.isPending;

  if (count === 0) return null;

  const handleBulkStatus = (completed: boolean) => {
    bulkUpdate.mutate(
      { todoIds: selectedIds, completed },
      {
        onSuccess: () => {
          onClearSelection();
        },
      }
    );
  };

  const handleBulkDelete = () => {
    if (
      window.confirm(
        `Are you sure you want to delete ${count} selected ${
          count === 1 ? "todo" : "todos"
        }? This action cannot be undone.`
      )
    ) {
      bulkDelete.mutate(
        { todoIds: selectedIds },
        {
          onSuccess: () => {
            onClearSelection();
          },
        }
      );
    }
  };

  return (
    <div className="flex items-center justify-between px-3 py-2 bg-primary/10 border border-primary/20 rounded-md animate-in slide-in-from-top-2 duration-200 mb-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-primary">
        <span>
          {count} {count === 1 ? "todo" : "todos"} selected
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1 border-primary/30 hover:bg-primary/20"
          onClick={() => handleBulkStatus(true)}
          disabled={isBusy}
        >
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
          Mark Completed
        </Button>

        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1 border-primary/30 hover:bg-primary/20"
          onClick={() => handleBulkStatus(false)}
          disabled={isBusy}
        >
          <Circle className="h-3.5 w-3.5 text-amber-500" />
          Mark Active
        </Button>

        <Button
          size="sm"
          variant="destructive"
          className="h-7 text-xs gap-1 cursor-pointer"
          onClick={handleBulkDelete}
          disabled={isBusy}
        >
          <Trash2 className="h-3.5 w-3.5" />
          Delete
        </Button>

        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={onClearSelection}
          disabled={isBusy}
          title="Clear selection"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

