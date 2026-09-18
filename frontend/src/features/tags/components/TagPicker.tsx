import { TagIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useTags, useAttachTag, useDetachTag } from "../api/tags";
import type { Tag } from "../api/tags";

interface TagPickerProps {
  todoId: string;
  attachedTags: Tag[];
}

export function TagPicker({ todoId, attachedTags }: TagPickerProps) {
  const { data: allTags } = useTags();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  const attachedIds = new Set(attachedTags.map((t) => t.id));

  const toggle = (tagId: string, isAttached: boolean) => {
    if (isAttached) {
      detachTag.mutate({ todoId, tagId });
    } else {
      attachTag.mutate({ todoId, tagId });
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          aria-label="Manage tags"
        >
          <TagIcon className="h-3.5 w-3.5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="end">
        <p className="text-xs font-medium text-muted-foreground px-1 pb-1">
          Attach tags
        </p>
        {!allTags || allTags.length === 0 ? (
          <p className="text-sm text-muted-foreground px-1 py-2">
            No tags yet. Create one from "Manage Tags".
          </p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {allTags.map((tag) => {
              const isAttached = attachedIds.has(tag.id);
              return (
                <label
                  key={tag.id}
                  className="flex items-center gap-2 rounded-sm px-1 py-1 text-sm hover:bg-accent/50 cursor-pointer"
                >
                  <Checkbox
                    checked={isAttached}
                    onCheckedChange={() => toggle(tag.id, isAttached)}
                  />
                  <Badge
                    style={{
                      borderColor: tag.color ?? undefined,
                      color: tag.color ?? undefined,
                    }}
                  >
                    {tag.name}
                  </Badge>
                </label>
              );
            })}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
