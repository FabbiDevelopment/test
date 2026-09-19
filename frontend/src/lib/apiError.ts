import { isAxiosError } from "axios";

interface ValidationIssue {
  msg?: unknown;
}

interface ApiErrorPayload {
  detail?: unknown;
}

function isApiErrorPayload(value: unknown): value is ApiErrorPayload {
  return typeof value === "object" && value !== null;
}

function getDetailMessage(detail: unknown): string | undefined {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const validationIssue = detail.find(
      (issue): issue is ValidationIssue =>
        typeof issue === "object" && issue !== null && "msg" in issue,
    );
    const message = validationIssue?.msg;
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  return undefined;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError<unknown>(error) || !isApiErrorPayload(error.response?.data)) {
    return fallback;
  }

  return getDetailMessage(error.response.data.detail) ?? fallback;
}
