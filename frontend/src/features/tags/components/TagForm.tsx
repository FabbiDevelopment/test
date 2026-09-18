import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTag, useUpdateTag, type Tag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";

const PRESET_COLORS = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#06b6d4",
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
];

interface TagFormProps {
  mode: "create" | "edit";
  tag?: Tag;
  onDone: () => void;
}

export function TagForm({ mode, tag, onDone }: TagFormProps) {
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: {
      name: tag?.name ?? "",
      color: tag?.color ?? "",
    },
  });

  const selectedColor = watch("color");

  const onSubmit = (data: TagFormData) => {
    const payload = { name: data.name, color: data.color || null };

    if (mode === "create") {
      createTag.mutate(payload, {
        onSuccess: () => {
          reset({ name: "", color: "" });
          onDone();
        },
      });
    } else if (tag) {
      updateTag.mutate(
        { id: tag.id, data: payload },
        { onSuccess: onDone }
      );
    }
  };

  const isPending = createTag.isPending || updateTag.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" data-testid="tag-form">
      <div className="space-y-2">
        <Label htmlFor="tag-name">Name</Label>
        <Input
          id="tag-name"
          placeholder="e.g. Work"
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive" role="alert">
            {errors.name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Color (optional)</Label>
        <div className="flex flex-wrap gap-2">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              aria-label={`Choose color ${c}`}
              onClick={() => setValue("color", c === selectedColor ? "" : c)}
              className={`h-6 w-6 rounded-full border-2 ${
                selectedColor === c ? "border-foreground" : "border-transparent"
              }`}
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
        {errors.color && (
          <p className="text-sm text-destructive" role="alert">
            {errors.color.message}
          </p>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-1">
        {mode === "edit" && (
          <Button type="button" variant="outline" size="sm" onClick={onDone}>
            Cancel
          </Button>
        )}
        <Button type="submit" size="sm" disabled={isPending}>
          {mode === "create" ? "Add tag" : "Save"}
        </Button>
      </div>
    </form>
  );
}
