"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { api } from "@/lib/api";
import type { User } from "@/types";

interface LoginCredentials {
  email: string;
  password: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  orgName?: string;
  planTier?: string;
}

export function useAuth() {
  const router = useRouter();
  const {
    user,
    isAuthenticated,
    isLoading,
    setUser,
    setLoading,
    logout: storeLogout,
  } = useAuthStore();

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setLoading(true);
      try {
        const response = await api.post("/api/v1/auth/login", {
          email: credentials.email,
          password: credentials.password,
          mfa_code: credentials.mfaCode,
        });
        const { access_token, user: userData } = response.data;
        localStorage.setItem("access_token", access_token);
        setUser(userData as User);
        router.push("/dashboard");
      } catch (error) {
        setLoading(false);
        throw error;
      }
      setLoading(false);
    },
    [router, setUser, setLoading]
  );

  const register = useCallback(
    async (data: RegisterData) => {
      setLoading(true);
      try {
        const response = await api.post("/api/v1/auth/register", {
          name: data.name,
          email: data.email,
          password: data.password,
          org_name: data.orgName,
          plan_tier: data.planTier,
        });
        const { access_token, user: userData } = response.data;
        localStorage.setItem("access_token", access_token);
        setUser(userData as User);
        router.push("/onboarding");
      } catch (error) {
        setLoading(false);
        throw error;
      }
      setLoading(false);
    },
    [router, setUser, setLoading]
  );

  const logout = useCallback(() => {
    storeLogout();
    router.push("/login");
  }, [storeLogout, router]);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        return;
      }
      const response = await api.get("/api/v1/auth/me");
      setUser(response.data as User);
    } catch {
      storeLogout();
    }
    setLoading(false);
  }, [setUser, setLoading, storeLogout]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
  };
}
