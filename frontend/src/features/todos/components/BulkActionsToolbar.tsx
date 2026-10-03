import { Button } from "@/components/ui/button";
import { useBulkUpdateTodoStatus } from "../api/todos";
import { Checkbox } from "@/components/ui/checkbox";

interface BulkActionsToolbarProps {
  selectedIds: string[];
  onClearSelection: () => void;
  allIds: string[];
  onSelectAll: (checked: boolean) => void;
}

export function BulkActionsToolbar({ selectedIds, onClearSelection, allIds, onSelectAll }: BulkActionsToolbarProps) {
  const bulkUpdate = useBulkUpdateTodoStatus();

  const handleBulkStatus = (completed: boolean) => {
    if (selectedIds.length === 0) return;
    bulkUpdate.mutate(
      { todo_ids: selectedIds, completed },
      {
        onSuccess: () => {
          onClearSelection();
        }
      }
    );
  };

  const isAllSelected = selectedIds.length > 0 && selectedIds.length === allIds.length;

  return (
    <div className="flex items-center gap-4 bg-accent/30 p-2 rounded-md mb-2 border">
      <div className="flex items-center gap-2 pl-1">
        <Checkbox 
          checked={isAllSelected} 
          onCheckedChange={(checked) => onSelectAll(checked as boolean)}
          id="select-all"
        />
        <label htmlFor="select-all" className="text-sm font-medium cursor-pointer">
          {selectedIds.length} selected
        </label>
      </div>

      <div className="flex-1" />

      {selectedIds.length > 0 && (
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleBulkStatus(true)}
            disabled={bulkUpdate.isPending}
          >
            Mark Completed
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleBulkStatus(false)}
            disabled={bulkUpdate.isPending}
          >
            Mark Active
          </Button>
        </div>
      )}
    </div>
  );
}
