import axios from "axios";
import { useAuthStore } from "@/lib/store";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Token refresh lock to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function refreshToken(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise;

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const storedRefreshToken =
        useAuthStore.getState().refreshToken ||
        (typeof window !== "undefined"
          ? localStorage.getItem("refresh_token")
          : null);

      if (!storedRefreshToken) return false;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/refresh`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: storedRefreshToken }),
        }
      );

      if (!response.ok) return false;

      const data = await response.json();
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only attempt refresh on 401 and if we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshed = await refreshToken();

      if (refreshed) {
        // Update the Authorization header with the new token and retry
        const newToken = localStorage.getItem("access_token");
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }

      // Refresh failed -- clear auth state and redirect to login
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        useAuthStore.getState().logout();
        window.location.href = "/login?returnTo=" + encodeURIComponent(window.location.pathname);
      }
    }

    return Promise.reject(error);
  }
);
