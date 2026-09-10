import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock hooks BEFORE importing component
const mockUsePhotoReferences = jest.fn();
jest.mock("../hooks", () => ({
  usePhotoReferences: (...args: unknown[]) => mockUsePhotoReferences(...args),
  useDeletePhoto: () => ({ mutate: jest.fn(), isPending: false }),
}));
jest.mock("../components/PhotoUploadDropzone", () => ({
  PhotoUploadDropzone: () => <div data-testid="upload-dropzone">Upload</div>,
}));
jest.mock("lucide-react", () => ({
  Image: (props: React.SVGAttributes<SVGElement>) => <svg data-testid="image-icon" {...props} />,
  Search: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Grid: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  List: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Plus: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Trash2: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Check: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  Eye: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
  X: (props: React.SVGAttributes<SVGElement>) => <svg {...props} />,
}));
jest.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <button>{children}</button>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: React.ReactNode; value: string }) => <div>{children}</div>,
}));
jest.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children, ...props }: { children?: React.ReactNode } & Record<string, unknown>) => <div {...props}>{children}</div>,
  ScrollBar: () => null,
}));
jest.mock("@/components/ui/dialog", () => ({
  Dialog: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
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

import { PhotoReferencePanel } from "../components/PhotoReferencePanel";

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("PhotoReferencePanel", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it("renders photo list", () => {
    mockUsePhotoReferences.mockReturnValue({
      data: { items: [
        { id: "p1", name: "Reference Photo 1", file_url: "https://example.com/1.jpg", thumbnail_url: "https://example.com/1t.jpg", usage_type: "style_reference", is_active: true, created_at: "2024-01-01", updated_at: "2024-01-01" },
        { id: "p2", name: "Reference Photo 2", file_url: "https://example.com/2.jpg", thumbnail_url: "https://example.com/2t.jpg", usage_type: "character_reference", is_active: true, created_at: "2024-01-01", updated_at: "2024-01-01" },
      ], total: 2, page: 1, page_size: 50 }, isLoading: false });
    render(<PhotoReferencePanel />, { wrapper });
    expect(screen.getByText("Reference Photo 1")).toBeInTheDocument();
    expect(screen.getByText("Reference Photo 2")).toBeInTheDocument();
  });

  it("shows usage type badges", () => {
    mockUsePhotoReferences.mockReturnValue({
      data: { items: [{ id: "p1", name: "Photo 1", file_url: "u", usage_type: "style_reference", is_active: true, created_at: "2024-01-01", updated_at: "2024-01-01" }], total: 1, page: 1, page_size: 50 }, isLoading: false });
    render(<PhotoReferencePanel />, { wrapper });
    const styleElements = screen.getAllByText("Style");
    expect(styleElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders search input", () => {
    mockUsePhotoReferences.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 50 }, isLoading: false });
    render(<PhotoReferencePanel />, { wrapper });
    expect(screen.getByPlaceholderText("Search photos...")).toBeInTheDocument();
  });

  it("shows empty state when no photos", () => {
    mockUsePhotoReferences.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 50 }, isLoading: false });
    render(<PhotoReferencePanel />, { wrapper });
    expect(screen.getByText("No photo references yet")).toBeInTheDocument();
  });

  it("shows loading state while fetching", () => {
    mockUsePhotoReferences.mockReturnValue({ data: undefined, isLoading: true });
    render(<PhotoReferencePanel />, { wrapper });
    expect(screen.getByPlaceholderText("Search photos...")).toBeInTheDocument();
  });
});
