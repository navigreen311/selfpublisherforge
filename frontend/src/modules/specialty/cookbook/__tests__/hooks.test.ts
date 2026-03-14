import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import { useCookbooks, useCookbookStats, useCookbook, useCookbookChapters, cookbookKeys } from "../hooks";

jest.mock("@/lib/api", () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), delete: jest.fn() } }));
jest.mock("@/hooks/use-api", () => ({ extractApiError: jest.fn((e: Error) => e.message || "Error") }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const { api } = require("@/lib/api");

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function W({ children }: { children: React.ReactNode }) { return React.createElement(QueryClientProvider, { client: qc }, children); };
}

describe("Cookbook hooks", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  describe("useCookbooks", () => {
    it("fetches cookbooks list", async () => {
      const mockData = { items: [], total: 0, page: 1, page_size: 20 };
      api.get.mockResolvedValueOnce({ data: mockData });
      const { result } = renderHook(() => useCookbooks(), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockData);
      expect(api.get).toHaveBeenCalledWith("/api/v1/specialty/cookbook-books", expect.any(Object));
    });
  });

  describe("useCookbookStats", () => {
    it("fetches cookbook stats", async () => {
      const mockStats = { total_cookbooks: 3, in_progress: 1, published: 2, total_recipes: 45 };
      api.get.mockResolvedValueOnce({ data: mockStats });
      const { result } = renderHook(() => useCookbookStats(), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockStats);
    });
  });

  describe("useCookbook", () => {
    it("fetches single cookbook", async () => {
      api.get.mockResolvedValueOnce({ data: { id: "456", title: "Test Cookbook" } });
      const { result } = renderHook(() => useCookbook("456"), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual({ id: "456", title: "Test Cookbook" });
    });
    it("does not fetch when id is empty", () => {
      const { result } = renderHook(() => useCookbook(""), { wrapper: createWrapper() });
      expect(result.current.isFetching).toBe(false);
    });
  });

  describe("useCookbookChapters", () => {
    it("fetches chapters", async () => {
      const chs = [{ id: "ch1", cookbook_id: "456", title: "Appetizers", order: 1, recipe_count: 5 }];
      api.get.mockResolvedValueOnce({ data: chs });
      const { result } = renderHook(() => useCookbookChapters("456"), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(chs);
    });
    it("does not fetch when cookbookId is empty", () => {
      const { result } = renderHook(() => useCookbookChapters(""), { wrapper: createWrapper() });
      expect(result.current.isFetching).toBe(false);
    });
  });

  describe("cookbookKeys", () => {
    it("generates correct query keys", () => {
      expect(cookbookKeys.all).toEqual(["cookbooks"]);
      expect(cookbookKeys.detail("456")).toEqual(["cookbooks", "detail", "456"]);
      expect(cookbookKeys.chapters("456")).toEqual(["cookbooks", "chapters", "456"]);
      expect(cookbookKeys.stats()).toEqual(["cookbooks", "stats"]);
    });
  });
});
