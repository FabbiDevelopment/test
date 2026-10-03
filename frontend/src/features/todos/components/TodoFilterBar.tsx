import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "../api/tags";
import type { TodoFilters } from "../api/todos";

interface TodoFilterBarProps {
  filters: TodoFilters;
  onChange: (filters: TodoFilters) => void;
  onOpenTags: () => void;
}

export function TodoFilterBar({ filters, onChange, onOpenTags }: TodoFilterBarProps) {
  const { data: tags = [] } = useTags();
  
  // Local state for debounced keyword searching
  const [keyword, setKeyword] = useState(filters.keyword || "");
  
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange({ ...filters, keyword: keyword || null, page: 1 });
    }, 500);
    return () => clearTimeout(timer);
  }, [keyword]); // eslint-disable-line

  const handleStatusChange = (val: string) => {
    let status: boolean | null = null;
    if (val === "completed") status = true;
    if (val === "active") status = false;
    onChange({ ...filters, status, page: 1 });
  };
  
  const currentStatusVal = filters.status === true ? "completed" : filters.status === false ? "active" : "all";

  return (
    <div className="flex flex-col sm:flex-row items-center gap-2 mb-4 w-full bg-card p-3 rounded-lg border">
      <Input 
        placeholder="Search todos..." 
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        className="flex-1 min-w-[200px]"
      />
      
      <select 
        value={currentStatusVal} 
        onChange={(e) => handleStatusChange(e.target.value)}
        className="flex h-10 w-[130px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="all">All</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
      </select>
      
      <select 
        value={filters.tag_id || "all"} 
        onChange={(e) => onChange({ ...filters, tag_id: e.target.value === "all" ? null : e.target.value, page: 1 })}
        className="flex h-10 w-[150px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="all">All Tags</option>
        {tags.map(tag => (
          <option key={tag.id} value={tag.id}>{tag.name}</option>
        ))}
      </select>

      <Button variant="outline" onClick={onOpenTags}>
        Manage Tags
      </Button>
    </div>
  );
}
