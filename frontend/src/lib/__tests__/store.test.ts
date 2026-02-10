/**
 * Tests for the Zustand auth store (useAuthStore).
 *
 * Uses spies on the real jsdom localStorage to validate persistence behaviour.
 */

import { useAuthStore } from "../store";
import type { User } from "@/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockUser: User = {
  id: "user-1",
  email: "test@example.com",
  name: "Test User",
  avatar_url: null,
  role: "owner" as User["role"],
  org_id: "org-1",
  is_active: true,
  last_login_at: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

// ---------------------------------------------------------------------------
// Spies on the real localStorage (jsdom provides one)
// ---------------------------------------------------------------------------

let setItemSpy: jest.SpyInstance;
let getItemSpy: jest.SpyInstance;
let removeItemSpy: jest.SpyInstance;

beforeEach(() => {
  setItemSpy = jest.spyOn(Storage.prototype, "setItem");
  getItemSpy = jest.spyOn(Storage.prototype, "getItem");
  removeItemSpy = jest.spyOn(Storage.prototype, "removeItem");
});

afterEach(() => {
  setItemSpy.mockRestore();
  getItemSpy.mockRestore();
  removeItemSpy.mockRestore();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useAuthStore", () => {
  beforeEach(() => {
    // Reset the store to default state between tests
    useAuthStore.setState({
      user: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,
    });
    localStorage.clear();
    jest.clearAllMocks();
  });

  // 1. Initial state is unauthenticated
  it("has correct initial state", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(true);
  });

  // 2. setAuth updates user and tokens
  describe("setUser", () => {
    it("sets the user and marks as authenticated", () => {
      useAuthStore.getState().setUser(mockUser);

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it("clears authentication when user is set to null", () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().setUser(null);

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("setTokens", () => {
    it("stores tokens in localStorage and state", () => {
      useAuthStore.getState().setTokens("access-123", "refresh-456");

      expect(setItemSpy).toHaveBeenCalledWith("access_token", "access-123");
      expect(setItemSpy).toHaveBeenCalledWith("refresh_token", "refresh-456");

      const state = useAuthStore.getState();
      expect(state.refreshToken).toBe("refresh-456");
    });
  });

  describe("setAuthenticated", () => {
    it("updates the isAuthenticated flag", () => {
      useAuthStore.getState().setAuthenticated(true);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      useAuthStore.getState().setAuthenticated(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe("setLoading", () => {
    it("updates the isLoading flag", () => {
      useAuthStore.getState().setLoading(false);
      expect(useAuthStore.getState().isLoading).toBe(false);

      useAuthStore.getState().setLoading(true);
      expect(useAuthStore.getState().isLoading).toBe(true);
    });
  });

  // 3. clearAuth resets state
  describe("logout", () => {
    it("clears user, refreshToken, isAuthenticated, and localStorage tokens", () => {
      // Set up authenticated state first
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().setTokens("access-123", "refresh-456");

      // Now logout
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);

      expect(removeItemSpy).toHaveBeenCalledWith("access_token");
      expect(removeItemSpy).toHaveBeenCalledWith("refresh_token");
    });
  });

  // 4. Persists to localStorage
  it("persists selected state to localStorage via zustand persist middleware", async () => {
    useAuthStore.getState().setUser(mockUser);
    useAuthStore.getState().setTokens("access-123", "refresh-456");

    // Zustand persist middleware may write asynchronously; flush microtasks.
    await new Promise((r) => setTimeout(r, 50));

    // Check that the persist middleware wrote to localStorage under "auth-storage".
    const raw = localStorage.getItem("auth-storage");
    expect(raw).toBeTruthy();

    const persisted = JSON.parse(raw!);
    expect(persisted.state).toMatchObject({
      user: mockUser,
      refreshToken: "refresh-456",
      isAuthenticated: true,
    });
  });

  // 5. Hydrates from localStorage on init
  it("hydrates from localStorage when store is initialised", async () => {
    // Simulate previously persisted data
    const persistedData = JSON.stringify({
      state: {
        user: mockUser,
        refreshToken: "persisted-refresh",
        isAuthenticated: true,
      },
      version: 0,
    });
    localStorage.setItem("auth-storage", persistedData);

    // Trigger rehydration
    await useAuthStore.persist.rehydrate();

    // Allow async hydration to complete
    await new Promise((r) => setTimeout(r, 50));

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.refreshToken).toBe("persisted-refresh");
    expect(state.isAuthenticated).toBe(true);
  });

  // Additional: combined setUser + setTokens workflow
  it("supports a full login workflow: setTokens then setUser", () => {
    useAuthStore.getState().setTokens("at-1", "rt-1");
    useAuthStore.getState().setUser(mockUser);
    useAuthStore.getState().setLoading(false);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.refreshToken).toBe("rt-1");
    expect(state.isLoading).toBe(false);
  });
});
