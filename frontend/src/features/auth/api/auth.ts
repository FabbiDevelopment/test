import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { clearSession, getSessionVersion, startSession } from "@/lib/session";

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function useLogin() {
  return useMutation({
    mutationFn: async (data: LoginRequest): Promise<TokenResponse> => {
      const response = await api.post("/auth/login", data);
      return response.data;
    },
    onSuccess: (data) => startSession(data.access_token, data.refresh_token),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest): Promise<TokenResponse> => {
      const response = await api.post("/auth/register", data);
      return response.data;
    },
    onSuccess: (data) => startSession(data.access_token, data.refresh_token),
  });
}

export function useLogout() {
  return useMutation({
    mutationFn: async () => {
      await api.post("/auth/logout");
    },
    onSettled: clearSession,
  });
}

interface UserResponse {
  id: string;
  email: string;
  created_at: string;
}

export async function fetchCurrentUser(signal?: AbortSignal): Promise<UserResponse> {
  const response = await api.get("/auth/me", { signal });
  return response.data;
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["currentUser", getSessionVersion()],
    queryFn: ({ signal }) => fetchCurrentUser(signal),
    enabled: !!localStorage.getItem("access_token"),
    retry: false,
  });
}
