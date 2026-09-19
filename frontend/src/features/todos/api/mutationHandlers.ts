import { todoKeys } from "./queryKeys.js";

export interface TodoQueryInvalidator {
  invalidateQueries: (filters: { queryKey: readonly unknown[] }) => Promise<unknown>;
}

export interface TodoMutationNotifier {
  success: (message: string) => unknown;
  error: (message: string) => unknown;
}

export interface BulkStatusResult {
  updated_count: number;
  completed: boolean;
}

export function bulkStatusSuccessMessage(result: BulkStatusResult): string {
  const suffix = result.updated_count === 1 ? "" : "s";
  const status = result.completed ? "completed" : "active";
  return `${result.updated_count} todo${suffix} marked ${status}`;
}

export async function handleBulkStatusSuccess(
  queryCache: TodoQueryInvalidator,
  notifier: TodoMutationNotifier,
  userId: string,
  result: BulkStatusResult,
): Promise<void> {
  await queryCache.invalidateQueries({ queryKey: todoKeys.user(userId) });
  notifier.success(bulkStatusSuccessMessage(result));
}

export function handleBulkStatusFailure(
  notifier: TodoMutationNotifier,
  message: string,
): void {
  notifier.error(message);
}
