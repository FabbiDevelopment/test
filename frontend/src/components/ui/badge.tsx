import * as React from "react"
import { cn } from "@/lib/utils"

function Badge({
  className,
  style,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="badge"
      style={style}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        className
      )}
      {...props}
    />
  )
}

export { Badge }
