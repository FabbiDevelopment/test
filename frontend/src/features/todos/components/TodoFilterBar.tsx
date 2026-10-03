import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "@/features/tags/api/tags";

interface TodoFilters {
  status?: "active" | "completed" | "";
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
}

interface TodoFilterBarProps {
  filters: TodoFilters;
  onChange: (filters: TodoFilters) => void;
}

export function TodoFilterBar({ filters, onChange }: TodoFilterBarProps) {
  const { data: tags } = useTags();

  const handleClear = () => {
    onChange({
      status: "",
      tag_id: "",
      keyword: "",
      date_from: "",
      date_to: "",
    });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 bg-muted/50 p-3 rounded-lg border">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search todos..."
          className="pl-9 h-9"
          value={filters.keyword || ""}
          onChange={(e) => onChange({ ...filters, keyword: e.target.value })}
        />
      </div>

      <select
        className="h-9 px-3 py-1 rounded-md border bg-background text-sm"
        value={filters.status || ""}
        onChange={(e) => onChange({ ...filters, status: e.target.value as any })}
      >
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
      </select>

      <select
        className="h-9 px-3 py-1 rounded-md border bg-background text-sm max-w-[150px]"
        value={filters.tag_id || ""}
        onChange={(e) => onChange({ ...filters, tag_id: e.target.value })}
      >
        <option value="">All Tags</option>
        {tags?.map((tag) => (
          <option key={tag.id} value={tag.id}>
            {tag.name}
          </option>
        ))}
      </select>

      <div className="flex items-center gap-2">
        <Input
          type="date"
          className="h-9 w-[140px] text-sm"
          value={filters.date_from || ""}
          onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
        />
        <span className="text-muted-foreground">-</span>
        <Input
          type="date"
          className="h-9 w-[140px] text-sm"
          value={filters.date_to || ""}
          onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
        />
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={handleClear}
        className="text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4 mr-1" />
        Clear
      </Button>
    </div>
  );
}
