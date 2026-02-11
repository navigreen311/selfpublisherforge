"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  ProfileListResponse,
  ProfileResponse,
  FingerprintResponse,
  CreateProfileRequest,
  AnalyzeRequest,
  GenerateSampleRequest,
  GenerateSampleResponse,
  ConformityCheckRequest,
  ConformityCheckResult,
} from "./types";

const API_PREFIX = "/api/v1/style-profiles";

// ── Query Keys ──────────────────────────────────────────────────

export const styleProfileKeys = {
  all: ["styleProfiles"] as const,
  lists: () => [...styleProfileKeys.all, "list"] as const,
  list: () => [...styleProfileKeys.lists()] as const,
  details: () => [...styleProfileKeys.all, "detail"] as const,
  detail: (id: string) => [...styleProfileKeys.details(), id] as const,
  fingerprint: (id: string) => [...styleProfileKeys.all, "fingerprint", id] as const,
};

// ── List Profiles ───────────────────────────────────────────────

export function useStyleProfiles() {
  return useQuery<ProfileListResponse>({
    queryKey: styleProfileKeys.list(),
    queryFn: async () => {
      const { data } = await api.get(API_PREFIX);
      return data;
    },
  });
}

// ── Get Profile Detail ──────────────────────────────────────────

export function useStyleProfile(id: string) {
  return useQuery<ProfileResponse>({
    queryKey: styleProfileKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// ── Get Fingerprint ─────────────────────────────────────────────

export function useStyleFingerprint(id: string) {
  return useQuery<FingerprintResponse>({
    queryKey: styleProfileKeys.fingerprint(id),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/${id}/fingerprint`);
      return data;
    },
    enabled: !!id,
  });
}

// ── Create Profile ──────────────────────────────────────────────

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation<ProfileResponse, Error, CreateProfileRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(API_PREFIX, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleProfileKeys.lists() });
    },
  });
}

// ── Analyze Profile ─────────────────────────────────────────────

export function useAnalyzeProfile(id: string) {
  const queryClient = useQueryClient();
  return useMutation<ProfileResponse, Error, AnalyzeRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/${id}/analyze`, request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleProfileKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: styleProfileKeys.fingerprint(id) });
    },
  });
}

// ── Generate Sample ─────────────────────────────────────────────

export function useGenerateSample(id: string) {
  return useMutation<GenerateSampleResponse, Error, GenerateSampleRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/${id}/generate-sample`, request);
      return data;
    },
  });
}

// ── Conformity Check ────────────────────────────────────────────

export function useConformityCheck(id: string) {
  return useMutation<ConformityCheckResult, Error, ConformityCheckRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post(`${API_PREFIX}/${id}/conformity-check`, request);
      return data;
    },
  });
}

// ── Delete Profile ──────────────────────────────────────────────

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`${API_PREFIX}/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: styleProfileKeys.lists() });
    },
  });
}
