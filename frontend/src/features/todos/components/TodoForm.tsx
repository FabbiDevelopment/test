import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCreateTodo, useUpdateTodo } from "../api/todos";
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

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoFormData>({
    resolver: zodResolver(todoSchema),
    defaultValues: {
      title: todo?.title || "",
      description: todo?.description || "",
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        title: todo?.title ?? "",
        description: todo?.description ?? "",
      });
    }
  }, [open, reset, todo]);

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
        { id: todo.id, userId: todo.user_id, data },
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
          <DialogDescription>
            {mode === "create"
              ? "Add a title and optional details for your new Todo."
              : "Update the title or details for this Todo."}
          </DialogDescription>
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

          <div className="flex justify-end gap-2">
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
