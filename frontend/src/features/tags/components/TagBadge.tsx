import type { Tag } from "../api/tags";
import { X } from "lucide-react";

interface TagBadgeProps {
  tag: Tag;
  onRemove?: () => void;
  className?: string;
}

export function TagBadge({ tag, onRemove, className = "" }: TagBadgeProps) {
  const color = tag.color || "#3B82F6";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border bg-card/60 ${className}`}
      style={{ borderColor: `${color}40` }}
    >
      <span
        className="h-2 w-2 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="truncate max-w-[120px]">{tag.name}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="hover:opacity-75 focus:outline-none ml-0.5 rounded-full p-0.5 text-muted-foreground hover:text-foreground"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}
