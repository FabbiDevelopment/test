import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Tag as TagIcon, Plus, X } from "lucide-react";
import type { Todo } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoItem({
  todo,
  isSelected,
  onSelect,
  onToggle,
  onEdit,
  onDelete,
  onAttachTag,
  onDetachTag,
}: TodoItemProps) {
  const { data: allTags = [] } = useTags();
  const [showTagPicker, setShowTagPicker] = useState(false);

  const attachedTagIds = new Set((todo.tags || []).map((t) => t.id));
  const availableTags = allTags.filter((t) => !attachedTagIds.has(t.id));

  return (
    <div
      className={`flex flex-col gap-2 p-3 rounded-lg border bg-card transition-colors group ${
        isSelected ? "border-primary/50 bg-primary/5" : "hover:bg-accent/40"
      }`}
    >
      <div className="flex items-center gap-3">
        {/* Bulk select checkbox */}
        <div className="flex items-center" title="Select for bulk action">
          <Checkbox
            id={`select-${todo.id}`}
            checked={isSelected}
            onCheckedChange={() => onSelect(todo.id)}
            className="data-[state=checked]:bg-primary"
          />
        </div>

        {/* Completion status checkbox */}
        <Checkbox
          id={`todo-${todo.id}`}
          checked={todo.completed}
          onCheckedChange={() => onToggle(todo)}
          className="rounded-full"
          title="Mark complete / active"
        />

        {/* Title & Description */}
        <div className="flex-1 min-w-0">
          <label
            htmlFor={`todo-${todo.id}`}
            className={`text-sm font-medium cursor-pointer block ${
              todo.completed ? "line-through text-muted-foreground" : ""
            }`}
          >
            {todo.title}
          </label>
          {todo.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
              {todo.description}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
          {/* Quick Tag Button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={() => setShowTagPicker(!showTagPicker)}
            title="Attach tag"
          >
            <TagIcon className="h-3.5 w-3.5" />
          </Button>

          {/* Edit Button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={() => onEdit(todo)}
            title="Edit todo"
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>

          {/* Delete Button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={() => onDelete(todo.id)}
            title="Delete todo"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Tags row */}
      <div className="flex items-center gap-1.5 flex-wrap pl-11">
        {todo.tags &&
          todo.tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border group/tag"
              style={{
                backgroundColor: `${tag.color || "#6366f1"}1a`,
                borderColor: tag.color || "#6366f1",
                color: tag.color || "#6366f1",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: tag.color || "#6366f1" }}
              />
              {tag.name}
              <button
                type="button"
                onClick={() => onDetachTag(todo.id, tag.id)}
                className="ml-0.5 opacity-60 hover:opacity-100"
                title={`Remove tag ${tag.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}

        {/* Tag Picker popup when toggled */}
        {showTagPicker && (
          <div className="flex items-center gap-1 flex-wrap bg-muted/90 p-1 rounded-md border text-xs animate-in fade-in duration-150">
            {availableTags.length === 0 ? (
              <span className="text-muted-foreground px-2 py-0.5 text-[11px]">
                {allTags.length === 0 ? "No tags created yet" : "All tags attached"}
              </span>
            ) : (
              availableTags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => {
                    onAttachTag(todo.id, tag.id);
                    setShowTagPicker(false);
                  }}
                  className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border bg-card hover:bg-accent transition-colors"
                  style={{
                    borderColor: tag.color || "#6366f1",
                    color: tag.color || "#6366f1",
                  }}
                >
                  <Plus className="h-2.5 w-2.5" />
                  {tag.name}
                </button>
              ))
            )}
            <button
              type="button"
              onClick={() => setShowTagPicker(false)}
              className="p-1 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
