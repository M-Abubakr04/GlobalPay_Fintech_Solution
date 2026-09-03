import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("globalpay_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers["X-Correlation-ID"] = crypto.randomUUID();
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("globalpay_token");
      localStorage.removeItem("globalpay_user");
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (detail) return JSON.stringify(detail);
    return error.message;
  }
  return error instanceof Error ? error.message : "Unexpected error";
}
