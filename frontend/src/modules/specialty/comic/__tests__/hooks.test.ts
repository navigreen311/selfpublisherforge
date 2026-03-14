import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import { useComics, useComicStats, useComic, comicKeys } from "../hooks";

jest.mock("@/lib/api", () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), delete: jest.fn() } }));
jest.mock("@/hooks/use-api", () => ({ extractApiError: jest.fn((e: Error) => e.message || "Error") }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn(), warning: jest.fn() } }));

const { api } = require("@/lib/api");

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function W({ children }: { children: React.ReactNode }) { return React.createElement(QueryClientProvider, { client: qc }, children); };
}

describe("Comic hooks", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  describe("useComics", () => {
    it("fetches comics list", async () => {
      const mockData = { items: [], total: 0, page: 1, page_size: 20 };
      api.get.mockResolvedValueOnce({ data: mockData });
      const { result } = renderHook(() => useComics(), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockData);
      expect(api.get).toHaveBeenCalledWith("/api/v1/specialty/comic-books", expect.any(Object));
    });
  });

  describe("useComicStats", () => {
    it("fetches comic stats", async () => {
      const mockStats = { total_comics: 5, in_progress: 2, published: 1, pages_created: 50, panels_created: 200 };
      api.get.mockResolvedValueOnce({ data: mockStats });
      const { result } = renderHook(() => useComicStats(), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockStats);
    });
  });

  describe("useComic", () => {
    it("fetches single comic", async () => {
      api.get.mockResolvedValueOnce({ data: { id: "123", title: "Test" } });
      const { result } = renderHook(() => useComic("123"), { wrapper: createWrapper() });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual({ id: "123", title: "Test" });
    });
    it("does not fetch when id is empty", () => {
      const { result } = renderHook(() => useComic(""), { wrapper: createWrapper() });
      expect(result.current.isFetching).toBe(false);
    });
  });

  describe("comicKeys", () => {
    it("generates correct query keys", () => {
      expect(comicKeys.all).toEqual(["comics"]);
      expect(comicKeys.detail("123")).toEqual(["comics", "detail", "123"]);
      expect(comicKeys.pages("123")).toEqual(["comics", "pages", "123"]);
      expect(comicKeys.characters("123")).toEqual(["comics", "characters", "123"]);
      expect(comicKeys.stats()).toEqual(["comics", "stats"]);
    });
  });
});
