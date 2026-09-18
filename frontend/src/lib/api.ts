import axios from "axios";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use((response) => response, (error) => {
  const isLoginRequest = error.config?.url === "/auth/login";
  if (error.response?.status === 401 && !isLoginRequest) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  }
  return Promise.reject(error);
});
