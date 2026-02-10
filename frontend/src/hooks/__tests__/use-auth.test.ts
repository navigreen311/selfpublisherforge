/**
 * Tests for the useAuth hook.
 *
 * We mock all external dependencies (next/navigation, zustand store, axios
 * api client) so we can test the hook logic in isolation.
 */

import { renderHook, act } from "@testing-library/react";
import type { User } from "@/types";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

const mockSetUser = jest.fn();
const mockSetTokens = jest.fn();
const mockSetLoading = jest.fn();
const mockStoreLogout = jest.fn();

let mockUser: User | null = null;
let mockIsAuthenticated = false;
let mockIsLoading = false;

jest.mock("@/lib/store", () => ({
  useAuthStore: jest.fn(() => ({
    user: mockUser,
    isAuthenticated: mockIsAuthenticated,
    isLoading: mockIsLoading,
    setUser: mockSetUser,
    setTokens: mockSetTokens,
    setLoading: mockSetLoading,
    logout: mockStoreLogout,
  })),
}));

const mockApiPost = jest.fn();
const mockApiGet = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    post: (...args: unknown[]) => mockApiPost(...args),
    get: (...args: unknown[]) => mockApiGet(...args),
  },
}));

// Import AFTER mocks
import { useAuth } from "../use-auth";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const fakeUser: User = {
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

// Keep original location for cleanup
const originalLocation = window.location;

beforeAll(() => {
  Object.defineProperty(window, "location", {
    writable: true,
    value: { ...originalLocation, href: "" },
  });
});

afterAll(() => {
  Object.defineProperty(window, "location", {
    writable: true,
    value: originalLocation,
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useAuth hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = null;
    mockIsAuthenticated = false;
    mockIsLoading = false;
    localStorage.clear();
    window.location.href = "";
  });

  // 1. Returns authenticated state when token exists
  it("returns authenticated state when user exists", () => {
    mockUser = fakeUser;
    mockIsAuthenticated = true;

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toEqual(fakeUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("returns unauthenticated state when no user", () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  // 2. Login stores token and user data
  it("login stores token and user data, then redirects to dashboard", async () => {
    mockApiPost.mockResolvedValueOnce({
      data: {
        access_token: "at-new",
        refresh_token: "rt-new",
        user: fakeUser,
      },
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login({
        email: "test@example.com",
        password: "password123",
      });
    });

    expect(mockApiPost).toHaveBeenCalledWith("/api/v1/auth/login", {
      email: "test@example.com",
      password: "password123",
      mfa_code: undefined,
    });
    expect(mockSetTokens).toHaveBeenCalledWith("at-new", "rt-new");
    expect(mockSetUser).toHaveBeenCalledWith(fakeUser);
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
    expect(mockSetLoading).toHaveBeenCalledWith(true);
  });

  it("login with MFA code passes mfa_code to the API", async () => {
    mockApiPost.mockResolvedValueOnce({
      data: {
        access_token: "at-mfa",
        refresh_token: "rt-mfa",
        user: fakeUser,
      },
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login({
        email: "test@example.com",
        password: "password123",
        mfaCode: "123456",
      });
    });

    expect(mockApiPost).toHaveBeenCalledWith("/api/v1/auth/login", {
      email: "test@example.com",
      password: "password123",
      mfa_code: "123456",
    });
  });

  it("login sets loading false and rethrows on API error", async () => {
    const apiError = new Error("Invalid credentials");
    mockApiPost.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useAuth());

    await expect(
      act(async () => {
        await result.current.login({
          email: "bad@example.com",
          password: "wrong",
        });
      })
    ).rejects.toThrow("Invalid credentials");

    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  // 3. Logout clears token and redirects
  it("logout clears auth state and redirects to /login", () => {
    const { result } = renderHook(() => useAuth());

    act(() => {
      result.current.logout();
    });

    expect(mockStoreLogout).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  // 4. Register creates account and logs in
  it("register creates account, stores tokens, and redirects to onboarding", async () => {
    mockApiPost.mockResolvedValueOnce({
      data: {
        access_token: "at-reg",
        refresh_token: "rt-reg",
        user: fakeUser,
      },
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.register({
        name: "Test User",
        email: "test@example.com",
        password: "securePassword1!",
        orgName: "My Org",
        planTier: "pro",
      });
    });

    expect(mockApiPost).toHaveBeenCalledWith("/api/v1/auth/register", {
      name: "Test User",
      email: "test@example.com",
      password: "securePassword1!",
      org_name: "My Org",
      plan_tier: "pro",
    });
    expect(mockSetTokens).toHaveBeenCalledWith("at-reg", "rt-reg");
    expect(mockSetUser).toHaveBeenCalledWith(fakeUser);
    expect(mockPush).toHaveBeenCalledWith("/onboarding");
  });

  it("register sets loading false and rethrows on API error", async () => {
    const apiError = new Error("Email already taken");
    mockApiPost.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useAuth());

    await expect(
      act(async () => {
        await result.current.register({
          name: "Test User",
          email: "existing@example.com",
          password: "securePassword1!",
        });
      })
    ).rejects.toThrow("Email already taken");

    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  // 5. checkAuth (token refresh / session check)
  it("checkAuth fetches current user when token exists", async () => {
    localStorage.setItem("access_token", "existing-token");
    mockApiGet.mockResolvedValueOnce({ data: fakeUser });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.checkAuth();
    });

    expect(mockSetLoading).toHaveBeenCalledWith(true);
    expect(mockApiGet).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(mockSetUser).toHaveBeenCalledWith(fakeUser);
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  it("checkAuth does nothing when no token in localStorage", async () => {
    localStorage.removeItem("access_token");

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.checkAuth();
    });

    expect(mockApiGet).not.toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  it("checkAuth calls logout on API error", async () => {
    localStorage.setItem("access_token", "expired-token");
    mockApiGet.mockRejectedValueOnce(new Error("Unauthorized"));

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.checkAuth();
    });

    expect(mockStoreLogout).toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  // 6. OAuth functions redirect correctly
  it("loginWithGoogle redirects to the Google OAuth endpoint", () => {
    const { result } = renderHook(() => useAuth());

    act(() => {
      result.current.loginWithGoogle();
    });

    expect(window.location.href).toBe(
      "http://localhost:8000/api/v1/auth/oauth/google"
    );
  });

  it("loginWithGitHub redirects to the GitHub OAuth endpoint", () => {
    const { result } = renderHook(() => useAuth());

    act(() => {
      result.current.loginWithGitHub();
    });

    expect(window.location.href).toBe(
      "http://localhost:8000/api/v1/auth/oauth/github"
    );
  });

  // handleOAuthCallback
  it("handleOAuthCallback exchanges code for tokens and redirects", async () => {
    mockApiPost.mockResolvedValueOnce({
      data: {
        access_token: "at-oauth",
        refresh_token: "rt-oauth",
        user: fakeUser,
      },
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.handleOAuthCallback("google", "auth-code-123");
    });

    expect(mockApiPost).toHaveBeenCalledWith(
      "/api/v1/auth/oauth/google/callback",
      { code: "auth-code-123" }
    );
    expect(mockSetTokens).toHaveBeenCalledWith("at-oauth", "rt-oauth");
    expect(mockSetUser).toHaveBeenCalledWith(fakeUser);
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("handleOAuthCallback sets loading false on error", async () => {
    mockApiPost.mockRejectedValueOnce(new Error("OAuth failed"));

    const { result } = renderHook(() => useAuth());

    await expect(
      act(async () => {
        await result.current.handleOAuthCallback("github", "bad-code");
      })
    ).rejects.toThrow("OAuth failed");

    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  // Return shape
  it("returns all expected functions and state", () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current).toHaveProperty("user");
    expect(result.current).toHaveProperty("isAuthenticated");
    expect(result.current).toHaveProperty("isLoading");
    expect(typeof result.current.login).toBe("function");
    expect(typeof result.current.register).toBe("function");
    expect(typeof result.current.logout).toBe("function");
    expect(typeof result.current.checkAuth).toBe("function");
    expect(typeof result.current.loginWithGoogle).toBe("function");
    expect(typeof result.current.loginWithGitHub).toBe("function");
    expect(typeof result.current.handleOAuthCallback).toBe("function");
  });
});
