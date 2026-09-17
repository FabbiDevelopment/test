import { Check, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";

interface BulkActionsProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onMarkCompleted: () => void;
  onMarkActive: () => void;
  allSelected: boolean;
}

export function BulkActions({
  selectedCount,
  onSelectAll,
  onDeselectAll,
  onMarkCompleted,
  onMarkActive,
  allSelected,
}: BulkActionsProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center gap-4 p-3 bg-muted/50 border-b text-sm animate-in fade-in slide-in-from-top-2">
      <div className="flex items-center gap-2">
        <Checkbox
          checked={allSelected}
          onCheckedChange={(checked) => {
            if (checked) onSelectAll();
            else onDeselectAll();
          }}
        />
        <span className="font-medium">{selectedCount} selected</span>
      </div>
      <div className="h-4 w-px bg-border" />
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onMarkCompleted}>
          <CheckCheck className="h-4 w-4 mr-1" />
          Mark Completed
        </Button>
        <Button variant="outline" size="sm" onClick={onMarkActive}>
          <Check className="h-4 w-4 mr-1" />
          Mark Active
        </Button>
      </div>
    </div>
  );
}
