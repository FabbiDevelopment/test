import { queryClient } from "@/lib/queryClient";
import { clearUserSession } from "@/lib/sessionCleanup";

export function clearAuthSession(): void {
  clearUserSession(localStorage, queryClient);
}
