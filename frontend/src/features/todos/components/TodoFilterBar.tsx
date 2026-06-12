import { Input } from "@/components/ui/input";
import { useTags } from "@/features/tags/api/tags";

interface FilterBarProps {
  filters: {
    keyword?: string;
    status?: string;
    tag_id?: string;
  };
  onFilterChange: (key: string, value: string | undefined) => void;
}

export function TodoFilterBar({ filters, onFilterChange }: FilterBarProps) {
  const { data: tags } = useTags();

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <Input
        placeholder="Search keyword..."
        value={filters.keyword || ""}
        onChange={(e) => onFilterChange("keyword", e.target.value || undefined)}
        className="flex-1 min-w-[200px]"
      />
      <select 
        value={filters.status || "all"} 
        onChange={(e) => onFilterChange("status", e.target.value === "all" ? undefined : e.target.value)}
        className="flex h-10 w-[120px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        <option value="all">All Status</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
      </select>

      {tags && tags.length > 0 && (
        <select 
          value={filters.tag_id || "all"} 
          onChange={(e) => onFilterChange("tag_id", e.target.value === "all" ? undefined : e.target.value)}
          className="flex h-10 w-[150px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <option value="all">All Tags</option>
          {tags.map(tag => (
            <option key={tag.id} value={tag.id}>{tag.name}</option>
          ))}
        </select>
      )}
    </div>
  );
}
