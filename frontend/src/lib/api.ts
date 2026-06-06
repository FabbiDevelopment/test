import axios from "axios";
import { clearAuthTokens, getAccessToken } from "@/features/auth/api/session";
import { queryClient } from "./queryClient";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach Bearer token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url ?? "";
    const isAuthFormRequest =
      requestUrl.endsWith("/auth/login") ||
      requestUrl.endsWith("/auth/register");
    const hadToken = Boolean(error.config?.headers?.Authorization);

    if (error.response?.status === 401 && hadToken && !isAuthFormRequest) {
      clearAuthTokens();
      queryClient.removeQueries({ queryKey: ["currentUser"] });
      queryClient.removeQueries({ queryKey: ["todos"] });
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
