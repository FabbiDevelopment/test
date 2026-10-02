import { queryClient } from "./queryClient";

let sessionVersion = 0;

export function getSessionVersion() {
  return sessionVersion;
}

export async function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  sessionVersion += 1;
  await queryClient.cancelQueries();
  queryClient.clear();
}

export async function startSession(accessToken: string, refreshToken: string) {
  await clearSession();
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}
