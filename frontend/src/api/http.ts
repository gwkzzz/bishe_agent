import axios, { AxiosError } from "axios";

export interface ApiError {
  message: string;
  status?: number;
  traceId?: string;
}

const defaultApiBaseUrl =
  typeof window === "undefined" ? "http://127.0.0.1:8000" : `${window.location.protocol}//${window.location.hostname}:8000`;

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl,
  timeout: 30_000
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function normalizeDetail(detail: unknown) {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String(item.msg);
        }
        return String(item);
      })
      .join("；");
  }
  return undefined;
}

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: unknown }>) => {
    const normalized: ApiError = {
      message: normalizeDetail(error.response?.data?.detail) ?? error.message,
      status: error.response?.status,
      traceId: error.response?.headers["x-trace-id"] as string | undefined
    };
    return Promise.reject(normalized);
  }
);
