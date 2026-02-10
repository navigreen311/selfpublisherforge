import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the API module ──────────────────────────────────────────────────

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

// ── Import hooks under test (after mocks) ────────────────────────────────

import {
  useCurrentUser,
  useUpdateProfile,
  useUpdatePreferences,
  useSessions,
  useRevokeSession,
  useOrg,
  useUpdateOrg,
  useOrgMembers,
  useInviteMember,
  useChangeMemberRole,
  useRemoveMember,
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
  userKeys,
} from "../hooks";

// ── Helpers ──────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockUserProfile = {
  id: "user-1",
  email: "test@example.com",
  name: "Test User",
  avatar_url: null,
  role: "owner",
  org_id: "org-1",
  preferences: { theme: "dark" },
  is_active: true,
  mfa_enabled: false,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockSessions = [
  {
    id: "sess-1",
    ip_address: "192.168.1.1",
    user_agent: "Mozilla/5.0",
    created_at: "2025-01-01T00:00:00Z",
    last_active_at: "2025-01-02T00:00:00Z",
  },
  {
    id: "sess-2",
    ip_address: "10.0.0.1",
    user_agent: "Chrome/120",
    created_at: "2025-01-03T00:00:00Z",
    last_active_at: null,
  },
];

const mockOrgDetails = {
  id: "org-1",
  name: "Test Org",
  slug: "test-org",
  plan_tier: "pro",
  logo_url: null,
  max_members: 10,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockOrgMembers = [
  {
    user_id: "user-1",
    email: "owner@example.com",
    name: "Owner",
    role: "owner",
    joined_at: "2025-01-01T00:00:00Z",
  },
  {
    user_id: "user-2",
    email: "member@example.com",
    name: "Member",
    role: "member",
    joined_at: "2025-01-15T00:00:00Z",
  },
];

const mockApiKeys = [
  {
    id: "key-1",
    name: "Production Key",
    prefix: "spf_prod",
    scopes: ["read", "write"],
    created_at: "2025-01-01T00:00:00Z",
    expires_at: "2026-01-01T00:00:00Z",
    last_used_at: "2025-06-01T00:00:00Z",
    is_active: true,
  },
];

const mockCreatedApiKey = {
  id: "key-new",
  name: "New Key",
  prefix: "spf_new",
  scopes: ["read"],
  created_at: "2025-06-01T00:00:00Z",
  expires_at: null,
  last_used_at: null,
  is_active: true,
  key: "spf_new_abc123xyz",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Users hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---------- Query key structure ----------

  describe("userKeys", () => {
    it("generates correct keys for me", () => {
      expect(userKeys.me).toEqual(["users", "me"]);
    });

    it("generates correct keys for sessions", () => {
      expect(userKeys.sessions).toEqual(["users", "me", "sessions"]);
    });

    it("generates correct keys for org", () => {
      expect(userKeys.org("org-1")).toEqual(["orgs", "org-1"]);
    });

    it("generates correct keys for members", () => {
      expect(userKeys.members("org-1")).toEqual(["orgs", "org-1", "members"]);
    });

    it("generates correct keys for apiKeys", () => {
      expect(userKeys.apiKeys("org-1")).toEqual([
        "orgs",
        "org-1",
        "api-keys",
      ]);
    });
  });

  // ---------- useCurrentUser ----------

  describe("useCurrentUser", () => {
    it("fetches the current user profile successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockUserProfile });

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/users/me");
      expect(result.current.data).toEqual(mockUserProfile);
    });

    it("handles errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Unauthorized");
    });
  });

  // ---------- useUpdateProfile ----------

  describe("useUpdateProfile", () => {
    it("updates user profile via PATCH", async () => {
      mockPatch.mockResolvedValueOnce({ data: { ...mockUserProfile, name: "Updated Name" } });

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ name: "Updated Name" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith("/api/v1/users/me", {
        name: "Updated Name",
      });
      expect(result.current.data?.name).toBe("Updated Name");
    });

    it("handles update errors", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Validation error"));

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ name: "" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Validation error");
    });
  });

  // ---------- useUpdatePreferences ----------

  describe("useUpdatePreferences", () => {
    it("updates user preferences via PATCH", async () => {
      const updatedProfile = {
        ...mockUserProfile,
        preferences: { theme: "light", language: "en" },
      };
      mockPatch.mockResolvedValueOnce({ data: updatedProfile });

      const { result } = renderHook(() => useUpdatePreferences(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ theme: "light", language: "en" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith("/api/v1/users/me/preferences", {
        preferences: { theme: "light", language: "en" },
      });
      expect(result.current.data?.preferences).toEqual({
        theme: "light",
        language: "en",
      });
    });

    it("handles preference update errors", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useUpdatePreferences(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ theme: "invalid" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Server error");
    });
  });

  // ---------- useSessions ----------

  describe("useSessions", () => {
    it("fetches sessions list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSessions });

      const { result } = renderHook(() => useSessions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/users/me/sessions");
      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].id).toBe("sess-1");
    });

    it("handles errors fetching sessions", async () => {
      mockGet.mockRejectedValueOnce(new Error("Forbidden"));

      const { result } = renderHook(() => useSessions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Forbidden");
    });
  });

  // ---------- useRevokeSession ----------

  describe("useRevokeSession", () => {
    it("revokes a session via DELETE", async () => {
      mockDelete.mockResolvedValueOnce({});

      const { result } = renderHook(() => useRevokeSession(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("sess-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/users/me/sessions/sess-1"
      );
    });

    it("handles revoke session errors", async () => {
      mockDelete.mockRejectedValueOnce(new Error("Session not found"));

      const { result } = renderHook(() => useRevokeSession(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("invalid-sess");
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Session not found");
    });
  });

  // ---------- useOrg ----------

  describe("useOrg", () => {
    it("fetches organization details successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockOrgDetails });

      const { result } = renderHook(() => useOrg("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/orgs/org-1");
      expect(result.current.data?.name).toBe("Test Org");
      expect(result.current.data?.plan_tier).toBe("pro");
    });

    it("does not fetch when orgId is empty", async () => {
      const { result } = renderHook(() => useOrg(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Not found"));

      const { result } = renderHook(() => useOrg("org-invalid"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Not found");
    });
  });

  // ---------- useUpdateOrg ----------

  describe("useUpdateOrg", () => {
    it("updates organization via PATCH", async () => {
      const updatedOrg = { ...mockOrgDetails, name: "Updated Org" };
      mockPatch.mockResolvedValueOnce({ data: updatedOrg });

      const { result } = renderHook(() => useUpdateOrg("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ name: "Updated Org" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith("/api/v1/orgs/org-1", {
        name: "Updated Org",
      });
      expect(result.current.data?.name).toBe("Updated Org");
    });

    it("handles update org errors", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Slug already taken"));

      const { result } = renderHook(() => useUpdateOrg("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ slug: "taken-slug" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Slug already taken");
    });
  });

  // ---------- useOrgMembers ----------

  describe("useOrgMembers", () => {
    it("fetches org members successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockOrgMembers });

      const { result } = renderHook(() => useOrgMembers("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/orgs/org-1/members");
      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].role).toBe("owner");
    });

    it("does not fetch when orgId is empty", async () => {
      const { result } = renderHook(() => useOrgMembers(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors fetching members", async () => {
      mockGet.mockRejectedValueOnce(new Error("Forbidden"));

      const { result } = renderHook(() => useOrgMembers("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Forbidden");
    });
  });

  // ---------- useInviteMember ----------

  describe("useInviteMember", () => {
    it("invites a member via POST", async () => {
      const inviteResponse = { message: "Invitation sent" };
      mockPost.mockResolvedValueOnce({ data: inviteResponse });

      const { result } = renderHook(() => useInviteMember("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ email: "new@example.com", role: "member" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/orgs/org-1/invite", {
        email: "new@example.com",
        role: "member",
      });
    });

    it("handles invite errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("User already a member"));

      const { result } = renderHook(() => useInviteMember("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ email: "existing@example.com", role: "member" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("User already a member");
    });
  });

  // ---------- useChangeMemberRole ----------

  describe("useChangeMemberRole", () => {
    it("changes member role via PATCH", async () => {
      const roleResponse = { message: "Role updated" };
      mockPatch.mockResolvedValueOnce({ data: roleResponse });

      const { result } = renderHook(() => useChangeMemberRole("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ userId: "user-2", role: "admin" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/orgs/org-1/members/user-2/role",
        { role: "admin" }
      );
    });

    it("handles role change errors", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Cannot change owner role"));

      const { result } = renderHook(() => useChangeMemberRole("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ userId: "user-1", role: "member" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Cannot change owner role");
    });
  });

  // ---------- useRemoveMember ----------

  describe("useRemoveMember", () => {
    it("removes a member via DELETE", async () => {
      mockDelete.mockResolvedValueOnce({});

      const { result } = renderHook(() => useRemoveMember("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("user-2");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/orgs/org-1/members/user-2"
      );
    });

    it("handles remove member errors", async () => {
      mockDelete.mockRejectedValueOnce(new Error("Cannot remove owner"));

      const { result } = renderHook(() => useRemoveMember("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("user-1");
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Cannot remove owner");
    });
  });

  // ---------- useApiKeys ----------

  describe("useApiKeys", () => {
    it("fetches API keys successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockApiKeys });

      const { result } = renderHook(() => useApiKeys("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/orgs/org-1/api-keys");
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].name).toBe("Production Key");
    });

    it("does not fetch when orgId is empty", async () => {
      const { result } = renderHook(() => useApiKeys(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors fetching API keys", async () => {
      mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

      const { result } = renderHook(() => useApiKeys("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Unauthorized");
    });
  });

  // ---------- useCreateApiKey ----------

  describe("useCreateApiKey", () => {
    it("creates an API key via POST", async () => {
      mockPost.mockResolvedValueOnce({ data: mockCreatedApiKey });

      const { result } = renderHook(() => useCreateApiKey("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          name: "New Key",
          scopes: ["read"],
          expires_in_days: null,
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/orgs/org-1/api-keys", {
        name: "New Key",
        scopes: ["read"],
        expires_in_days: null,
      });
      expect(result.current.data?.key).toBe("spf_new_abc123xyz");
    });

    it("handles API key creation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Key limit reached"));

      const { result } = renderHook(() => useCreateApiKey("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ name: "Another Key" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Key limit reached");
    });
  });

  // ---------- useRevokeApiKey ----------

  describe("useRevokeApiKey", () => {
    it("revokes an API key via DELETE", async () => {
      mockDelete.mockResolvedValueOnce({});

      const { result } = renderHook(() => useRevokeApiKey("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("key-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/orgs/org-1/api-keys/key-1"
      );
    });

    it("handles revoke API key errors", async () => {
      mockDelete.mockRejectedValueOnce(new Error("Key not found"));

      const { result } = renderHook(() => useRevokeApiKey("org-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("invalid-key");
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Key not found");
    });
  });

  // ---------- Data structure correctness ----------

  describe("data structure correctness", () => {
    it("verifies user profile data structure is preserved", async () => {
      mockGet.mockResolvedValueOnce({ data: mockUserProfile });

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const user = result.current.data!;
      expect(typeof user.id).toBe("string");
      expect(typeof user.email).toBe("string");
      expect(typeof user.name).toBe("string");
      expect(typeof user.role).toBe("string");
      expect(typeof user.is_active).toBe("boolean");
      expect(typeof user.mfa_enabled).toBe("boolean");
      expect(user.preferences).toBeDefined();
    });

    it("verifies session data structure", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSessions });

      const { result } = renderHook(() => useSessions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const sessions = result.current.data!;
      expect(sessions).toBeInstanceOf(Array);
      sessions.forEach((session) => {
        expect(session).toHaveProperty("id");
        expect(session).toHaveProperty("created_at");
      });
    });

    it("verifies org members data structure", async () => {
      mockGet.mockResolvedValueOnce({ data: mockOrgMembers });

      const { result } = renderHook(() => useOrgMembers("org-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const members = result.current.data!;
      expect(members).toBeInstanceOf(Array);
      members.forEach((member) => {
        expect(member).toHaveProperty("user_id");
        expect(member).toHaveProperty("email");
        expect(member).toHaveProperty("role");
        expect(typeof member.role).toBe("string");
      });
    });
  });
});
