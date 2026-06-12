import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCreateTodo, useUpdateTodo } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";
import { todoSchema, type TodoFormData } from "../schemas/todo";
import type { Todo } from "../api/todos";

interface TodoFormProps {
  mode: "create" | "edit";
  todo?: Todo;
  open: boolean;
  onClose: () => void;
}

export function TodoForm({ mode, todo, open, onClose }: TodoFormProps) {
  const createTodo = useCreateTodo();
  const updateTodo = useUpdateTodo();
  const { data: tags } = useTags();

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<TodoFormData>({
    resolver: zodResolver(todoSchema),
    defaultValues: {
      title: todo?.title || "",
      description: todo?.description || "",
      tag_ids: todo?.tags?.map((t) => t.id) || [],
    },
  });

  const onSubmit = (data: TodoFormData) => {
    if (mode === "create") {
      createTodo.mutate(data, {
        onSuccess: () => {
          reset();
          onClose();
        },
      });
    } else if (todo) {
      updateTodo.mutate(
        { id: todo.id, data },
        {
          onSuccess: () => {
            onClose();
          },
        }
      );
    }
  };

  const isPending = createTodo.isPending || updateTodo.isPending;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create Todo" : "Edit Todo"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="What needs to be done?"
              {...register("title")}
            />
            {errors.title && (
              <p className="text-sm text-destructive">
                {errors.title.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Input
              id="description"
              placeholder="Add details..."
              {...register("description")}
            />
            {errors.description && (
              <p className="text-sm text-destructive">
                {errors.description.message}
              </p>
            )}
          </div>

          {tags && tags.length > 0 && (
            <div className="space-y-2">
              <Label>Tags</Label>
              <div className="flex flex-wrap gap-3 p-2 border rounded-md max-h-32 overflow-y-auto">
                <Controller
                  name="tag_ids"
                  control={control}
                  render={({ field }) => (
                    <>
                      {tags.map((tag) => {
                        const isChecked = field.value?.includes(tag.id);
                        return (
                          <div key={tag.id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`tag-${tag.id}`}
                              checked={isChecked}
                              onCheckedChange={(checked) => {
                                const current = field.value || [];
                                if (checked) {
                                  field.onChange([...current, tag.id]);
                                } else {
                                  field.onChange(current.filter((id) => id !== tag.id));
                                }
                              }}
                            />
                            <label
                              htmlFor={`tag-${tag.id}`}
                              className="text-sm font-medium leading-none cursor-pointer flex items-center gap-1"
                            >
                              <div 
                                className="w-2.5 h-2.5 rounded-full" 
                                style={{ backgroundColor: tag.color || "#ccc" }} 
                              />
                              {tag.name}
                            </label>
                          </div>
                        );
                      })}
                    </>
                  )}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending
                ? mode === "create"
                  ? "Creating..."
                  : "Saving..."
                : mode === "create"
                ? "Create"
                : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
