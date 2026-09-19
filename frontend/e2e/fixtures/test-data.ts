export const E2E_PASSWORD = "E2eTodo@123";
export const E2E_API_BASE_URL = "http://127.0.0.1:8000";

export type E2EAccountRole =
  | "journey1"
  | "journey2-a"
  | "journey2-b"
  | "tier4"
  | "pagination";

export function e2eAccount(role: E2EAccountRole, retry: number) {
  return {
    email: `e2e-${role}-r${retry}@example.com`,
    password: E2E_PASSWORD,
  } as const;
}

export function e2eTodoTitle(journey: 1 | 2, retry: number): string {
  return `E2E Journey ${journey} Todo r${retry}`;
}
