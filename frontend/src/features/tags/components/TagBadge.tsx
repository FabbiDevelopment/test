import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Tag } from "../api/tags";

interface TagBadgeProps {
  tag: Tag;
  onRemove?: () => void;
  className?: string;
}

export function TagBadge({ tag, onRemove, className }: TagBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
        className
      )}
      style={{
        backgroundColor: tag.color ? `${tag.color}20` : "hsl(var(--muted))",
        color: tag.color || "hsl(var(--muted-foreground))",
        border: `1px solid ${tag.color ? `${tag.color}40` : "hsl(var(--border))"}`,
      }}
    >
      {tag.name}
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="hover:opacity-70 transition-opacity"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}
