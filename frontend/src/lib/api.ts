import axios from "axios";
import { clearSession } from "./session";

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
  async (error) => {
    const token = localStorage.getItem("access_token");
    if (
      error.response?.status === 401 &&
      token &&
      error.config?.headers?.Authorization === `Bearer ${token}`
    ) {
      await clearSession();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
