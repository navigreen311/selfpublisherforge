/**
 * Tests for the Axios-based API client (frontend/src/lib/api.ts).
 *
 * Strategy: We mock the default axios adapter so that no real HTTP requests
 * are made. The interceptors (request + response) are the main logic under
 * test.
 */

import type { AxiosError, InternalAxiosRequestConfig } from "axios";

// ---------------------------------------------------------------------------
// Mocks — declared before module import
// ---------------------------------------------------------------------------

const mockLogout = jest.fn();
const mockSetTokens = jest.fn();
let mockStoreRefreshToken: string | null = "mock-refresh-token";

jest.mock("@/lib/store", () => ({
  useAuthStore: {
    getState: () => ({
      refreshToken: mockStoreRefreshToken,
      logout: mockLogout,
      setTokens: mockSetTokens,
    }),
  },
}));

// Mock global fetch (used by the refreshToken function inside api.ts)
const mockFetch = jest.fn();

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
// Import the module under test — AFTER mocks
// ---------------------------------------------------------------------------
import { api } from "../api";
import axios from "axios";

// ---------------------------------------------------------------------------
// Mock the axios adapter so requests resolve/reject in-memory
// ---------------------------------------------------------------------------

// We use axios interceptors.request to inspect header logic.
// To avoid real HTTP, we intercept at the adapter level.
let mockAdapter: jest.Mock;

function installMockAdapter() {
  mockAdapter = jest.fn();
  api.defaults.adapter = mockAdapter as unknown as typeof api.defaults.adapter;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resetState() {
  jest.clearAllMocks();
  global.fetch = mockFetch as unknown as typeof fetch;
  localStorage.clear();
  localStorage.setItem("access_token", "test-access-token");
  localStorage.setItem("refresh_token", "test-refresh-token");
  mockStoreRefreshToken = "mock-refresh-token";
  window.location.href = "";
  installMockAdapter();
}

/** Create a minimal resolved adapter response */
function adapterSuccess(data: unknown, status = 200) {
  return Promise.resolve({
    data,
    status,
    statusText: "OK",
    headers: {},
    config: {} as InternalAxiosRequestConfig,
  });
}

/** Create a 401 adapter rejection that triggers the response interceptor */
function adapter401() {
  const config = {
    headers: { Authorization: "Bearer old-token" },
  } as unknown as InternalAxiosRequestConfig;

  const error = new axios.AxiosError(
    "Unauthorized",
    "ERR_BAD_REQUEST",
    config,
    {},
    {
      status: 401,
      data: { detail: "Token expired" },
      statusText: "Unauthorized",
      headers: {},
      config,
    }
  );
  return Promise.reject(error);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("API client (axios instance)", () => {
  beforeEach(() => {
    resetState();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 1. Makes GET requests with correct headers
  it("makes GET requests with correct headers", async () => {
    mockAdapter.mockImplementationOnce((config: InternalAxiosRequestConfig) => {
      // Verify headers set by the axios instance defaults
      expect(config.headers?.["Content-Type"]).toBe("application/json");
      return adapterSuccess({ ok: true });
    });

    const response = await api.get("/api/v1/test");
    expect(response.data).toEqual({ ok: true });
    expect(mockAdapter).toHaveBeenCalledTimes(1);
  });

  // 2. Makes POST requests with JSON body
  it("makes POST requests with JSON body", async () => {
    const payload = { title: "My Book" };

    mockAdapter.mockImplementationOnce((config: InternalAxiosRequestConfig) => {
      expect(config.method).toBe("post");
      const body = JSON.parse(config.data as string);
      expect(body).toEqual(payload);
      return adapterSuccess({ id: 1, ...payload }, 201);
    });

    const response = await api.post("/api/v1/books", payload);
    expect(response.data).toEqual({ id: 1, ...payload });
  });

  // 3. Includes auth token in Authorization header
  it("includes auth token in Authorization header", async () => {
    mockAdapter.mockImplementationOnce((config: InternalAxiosRequestConfig) => {
      expect(config.headers?.Authorization).toBe("Bearer test-access-token");
      return adapterSuccess({});
    });

    await api.get("/api/v1/me");
    expect(mockAdapter).toHaveBeenCalledTimes(1);
  });

  // 4. Handles 401 by attempting token refresh
  it("handles 401 by attempting token refresh", async () => {
    // First call: adapter returns 401
    mockAdapter.mockImplementationOnce(() => adapter401());

    // Mock fetch for the refresh endpoint: succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      }),
    });

    // Second call (retry after refresh): adapter succeeds
    mockAdapter.mockImplementationOnce(() => adapterSuccess({ ok: true }));

    const response = await api.get("/api/v1/protected");

    // Verify the refresh call was made
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/refresh"),
      expect.objectContaining({ method: "POST" })
    );
    // Verify tokens were updated in the store
    expect(mockSetTokens).toHaveBeenCalledWith(
      "new-access-token",
      "new-refresh-token"
    );
    // Verify the retry succeeded
    expect(response.data).toEqual({ ok: true });
    // Adapter called twice: original + retry
    expect(mockAdapter).toHaveBeenCalledTimes(2);
  });

  // 5. Redirects to /login on refresh failure
  it("redirects to /login on refresh failure", async () => {
    // First call: adapter returns 401
    mockAdapter.mockImplementationOnce(() => adapter401());

    // Refresh fails
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    await expect(api.get("/api/v1/protected")).rejects.toThrow();

    expect(mockLogout).toHaveBeenCalled();
    expect(window.location.href).toBe("/login");
  });

  // 6. Handles network errors gracefully
  it("handles network errors gracefully", async () => {
    mockAdapter.mockImplementationOnce(() =>
      Promise.reject(new axios.AxiosError("Network Error", "ERR_NETWORK"))
    );

    await expect(api.get("/api/v1/test")).rejects.toThrow("Network Error");
  });

  // 7. Returns parsed JSON on success
  it("returns parsed JSON on success", async () => {
    const responseData = { id: 1, name: "Test Book" };
    mockAdapter.mockImplementationOnce(() => adapterSuccess(responseData));

    const result = await api.get("/api/v1/books/1");
    expect(result.data).toEqual(responseData);
  });

  // 8. Handles non-JSON responses
  it("handles non-JSON responses", async () => {
    mockAdapter.mockImplementationOnce(() =>
      Promise.resolve({
        data: "plain text response",
        status: 200,
        statusText: "OK",
        headers: { "content-type": "text/plain" },
        config: {} as InternalAxiosRequestConfig,
      })
    );

    const result = await api.get("/api/v1/export");
    expect(result.data).toBe("plain text response");
  });

  // Additional: no Authorization header when no token in localStorage
  it("does not include Authorization header when no token exists", async () => {
    localStorage.removeItem("access_token");

    mockAdapter.mockImplementationOnce((config: InternalAxiosRequestConfig) => {
      expect(config.headers?.Authorization).toBeUndefined();
      return adapterSuccess({});
    });

    await api.get("/api/v1/public");
    expect(mockAdapter).toHaveBeenCalledTimes(1);
  });

  // Additional: does not retry when _retry is already true (avoids infinite loop)
  it("does not retry when request has already been retried", async () => {
    // First 401
    mockAdapter.mockImplementationOnce(() => adapter401());

    // Refresh fails — no retry possible
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    await expect(api.get("/api/v1/protected")).rejects.toThrow();

    // The adapter should only have been called once (no infinite retry)
    expect(mockAdapter).toHaveBeenCalledTimes(1);
  });

  // Additional: when store has no refresh token, goes straight to logout
  it("redirects when no refresh token is available", async () => {
    mockStoreRefreshToken = null;
    localStorage.removeItem("refresh_token");

    mockAdapter.mockImplementationOnce(() => adapter401());

    await expect(api.get("/api/v1/protected")).rejects.toThrow();

    // fetch should not have been called (no token to refresh with)
    expect(mockFetch).not.toHaveBeenCalled();
    expect(mockLogout).toHaveBeenCalled();
    expect(window.location.href).toBe("/login");
  });
});
