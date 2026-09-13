import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockUseStyleClones = jest.fn();
jest.mock("../hooks", () => ({
  useStyleClones: (...args: unknown[]) => mockUseStyleClones(...args),
  useDeleteStyleClone: () => ({ mutate: jest.fn(), isPending: false }),
  useAnalyzeStyle: () => ({ mutate: jest.fn(), isPending: false }),
  useTestGenerate: () => ({ mutate: jest.fn(), isPending: false }),
  useCheckDrift: () => ({ mutate: jest.fn(), isPending: false }),
  useSetDefault: () => ({ mutate: jest.fn(), isPending: false }),
}));
jest.mock("../components/StyleCloneCreator", () => ({
  StyleCloneCreator: () => <div data-testid="style-creator">Creator</div>,
}));
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Palette: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Plus: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Search: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Trash2: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Eye: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Wand2: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  AlertTriangle: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Star: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  BarChart3: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
}));
jest.mock("@radix-ui/react-slot", () => ({
  // @radix-ui/react-primitive calls createSlot() at module load, so a mock
  // without it throws before any test in the file runs.
  createSlot: () =>
    React.forwardRef(function MockSlot(
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLElement>
    ) {
      return React.isValidElement(children)
        ? React.cloneElement(children, { ...props, ref } as Record<string, unknown>)
        : React.createElement("span", { ref, ...props }, children as React.ReactNode);
    }),
  createSlottable: () =>
    function MockSlottable({ children }: { children?: React.ReactNode }) {
      return children as React.ReactElement;
    },
  Slot: React.forwardRef(({ children, ...props }: { children?: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => {
    if (React.isValidElement(children)) return React.cloneElement(children, { ...props, ref } as Record<string, unknown>);
    return <div ref={ref} {...props}>{children}</div>;
  }),
}));
jest.mock("@/components/ui/dialog", () => ({
  Dialog: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogTrigger: React.forwardRef(({ children, ...props }: { children?: React.ReactNode; asChild?: boolean } & Record<string, unknown>, _ref: React.Ref<HTMLElement>) => <div {...props}>{children}</div>),
}));

import { StyleCloneManager } from "../components/StyleCloneManager";

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("StyleCloneManager", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it("renders style profile list", () => {
    mockUseStyleClones.mockReturnValue({ data: { items: [
      { id: "s1", name: "Watercolor Style", description: "Soft watercolor", reference_image_urls: ["u"], reference_count: 5, is_active: true, is_default: true, times_used: 42, drift_score: 0.08, created_at: "2024-01-01", updated_at: "2024-01-01" },
      { id: "s2", name: "Manga Style", description: "Clean manga line art", reference_image_urls: [], reference_count: 3, is_active: true, is_default: false, times_used: 15, drift_score: 0.22, created_at: "2024-01-01", updated_at: "2024-01-01" },
    ], total: 2, page: 1, page_size: 50 }, isLoading: false });
    render(<StyleCloneManager />, { wrapper });
    expect(screen.getByText("Watercolor Style")).toBeInTheDocument();
    expect(screen.getByText("Manga Style")).toBeInTheDocument();
  });

  it("shows usage count", () => {
    mockUseStyleClones.mockReturnValue({ data: { items: [
      { id: "s1", name: "Watercolor Style", description: "Soft", reference_image_urls: [], reference_count: 5, is_active: true, is_default: false, times_used: 42, drift_score: 0.08, created_at: "2024-01-01", updated_at: "2024-01-01" },
    ], total: 1, page: 1, page_size: 50 }, isLoading: false });
    render(<StyleCloneManager />, { wrapper });
    expect(screen.getByText(/42 time/)).toBeInTheDocument();
  });

  it("renders search input", () => {
    mockUseStyleClones.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 50 }, isLoading: false });
    render(<StyleCloneManager />, { wrapper });
    expect(screen.getByPlaceholderText("Search style profiles...")).toBeInTheDocument();
  });

  it("renders create button", () => {
    mockUseStyleClones.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 50 }, isLoading: false });
    render(<StyleCloneManager />, { wrapper });
    expect(screen.getByText("Create New")).toBeInTheDocument();
  });

  it("shows empty state when no profiles", () => {
    mockUseStyleClones.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 50 }, isLoading: false });
    render(<StyleCloneManager />, { wrapper });
    expect(screen.getByText("No style profiles yet")).toBeInTheDocument();
  });

  it("shows loading skeletons while fetching", () => {
    mockUseStyleClones.mockReturnValue({ data: undefined, isLoading: true });
    render(<StyleCloneManager />, { wrapper });
    expect(document.querySelectorAll("[class*=animate-pulse]").length).toBeGreaterThanOrEqual(1);
  });
});
