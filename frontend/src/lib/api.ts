import axios from "axios";
import { queryClient } from "@/lib/queryClient";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const currentUserQueryKey = ["currentUser"] as const;
const todosQueryKey = ["todos"] as const;

function clearAuthState() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  queryClient.removeQueries({ queryKey: currentUserQueryKey });
  queryClient.removeQueries({ queryKey: todosQueryKey });
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
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
    const isLoginRequest = requestUrl.includes("/auth/login");
    const isRegisterRequest = requestUrl.includes("/auth/register");

    if (
      error.response?.status === 401 &&
      !isLoginRequest &&
      !isRegisterRequest
    ) {
      clearAuthState();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
