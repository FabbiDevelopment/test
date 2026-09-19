const AUTH_FORM_ENDPOINTS = new Set(["/auth/login", "/auth/register"]);

/**
 * Login and registration own their 401 responses so their forms can display a
 * useful error. Every other 401 represents an invalid authenticated session.
 */
export function shouldClearSessionForUnauthorized(
  status: number | undefined,
  requestUrl: string | undefined,
): boolean {
  if (status !== 401) {
    return false;
  }

  const pathname = requestUrl?.split("?")[0];
  return !pathname || !AUTH_FORM_ENDPOINTS.has(pathname);
}
