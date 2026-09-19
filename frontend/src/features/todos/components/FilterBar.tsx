import { useState, useEffect } from "react";
import { Search, X, Filter, Tag as TagIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTags } from "@/features/tags/api/tagsApi";
import type { TodoFilterParams } from "../api/todos";

interface FilterBarProps {
  filters: TodoFilterParams;
  onFilterChange: (newFilters: TodoFilterParams) => void;
  onClearFilters: () => void;
  onOpenTagManager: () => void;
}

export function FilterBar({
  filters,
  onFilterChange,
  onClearFilters,
  onOpenTagManager,
}: FilterBarProps) {
  const { data: tags = [] } = useTags();
  const [keywordInput, setKeywordInput] = useState(filters.keyword || "");

  useEffect(() => {
    setKeywordInput(filters.keyword || "");
  }, [filters.keyword]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if ((filters.keyword || "") !== keywordInput) {
        onFilterChange({ ...filters, keyword: keywordInput || undefined, page: 1 });
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [keywordInput]);

  const hasActiveFilters = Boolean(
    filters.keyword ||
    filters.status ||
    filters.tag_id ||
    filters.date_from ||
    filters.date_to
  );

  return (
    <div className="space-y-3 bg-muted/30 p-4 rounded-xl border">
      { }
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground/80">
          <Filter className="h-4 w-4 text-primary" />
          <span>Bộ lọc công việc</span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenTagManager}
            className="h-8 gap-1.5 text-xs border-primary/30 hover:border-primary"
          >
            <TagIcon className="h-3.5 w-3.5 text-primary" />
            <span>Quản lý thẻ</span>
          </Button>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearFilters}
              className="h-8 gap-1 text-xs text-muted-foreground hover:text-destructive"
            >
              <X className="h-3.5 w-3.5" />
              <span>Xóa bộ lọc</span>
            </Button>
          )}
        </div>
      </div>


      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Tìm theo từ khóa..."
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            className="pl-8 pr-8 h-9 text-xs bg-background"
          />
          {keywordInput && (
            <button
              onClick={() => {
                setKeywordInput("");
                onFilterChange({ ...filters, keyword: undefined, page: 1 });
              }}
              className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div>
          <select
            value={filters.status || "all"}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                status: e.target.value === "all" ? undefined : e.target.value,
                page: 1,
              })
            }
            className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="pending">Chưa hoàn thành</option>
            <option value="completed">Đã hoàn thành</option>
          </select>
        </div>

        <div>
          <select
            value={filters.tag_id || "all"}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                tag_id: e.target.value === "all" ? undefined : e.target.value,
                page: 1,
              })
            }
            className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="all">Tất cả thẻ Tag</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                🏷️ {tag.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="relative flex-1">
            <Input
              type="date"
              title="Từ ngày"
              value={filters.date_from ? filters.date_from.split("T")[0] : ""}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  date_from: e.target.value ? `${e.target.value}T00:00:00Z` : undefined,
                  page: 1,
                })
              }
              className="h-9 text-xs bg-background px-2"
            />
          </div>
          <span className="text-xs text-muted-foreground">-</span>
          <div className="relative flex-1">
            <Input
              type="date"
              title="Đến ngày"
              value={filters.date_to ? filters.date_to.split("T")[0] : ""}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  date_to: e.target.value ? `${e.target.value}T23:59:59Z` : undefined,
                  page: 1,
                })
              }
              className="h-9 text-xs bg-background px-2"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
