import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: jest.fn() }),
  usePathname: () => "/cover-design",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ id: "cover-1" }),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  Plus: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-plus" {...props} />
  ),
  Palette: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-palette" {...props} />
  ),
  ImageIcon: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-image" {...props} />
  ),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-loader" {...props} />
  ),
  ArrowLeft: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-arrow-left" {...props} />
  ),
  Sparkles: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-sparkles" {...props} />
  ),
  Download: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-download" {...props} />
  ),
  Trash2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trash" {...props} />
  ),
  Wand2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-wand" {...props} />
  ),
  Image: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-image-base" {...props} />
  ),
}));

// Mock the cover-design hooks
const mockUseCovers = jest.fn();
const mockUseCover = jest.fn();
const mockUseGenerateCover = jest.fn();
const mockUseDeleteCover = jest.fn();
const mockUseCoverTemplates = jest.fn();

jest.mock("@/modules/cover-design/hooks", () => ({
  useCovers: (...args: unknown[]) => mockUseCovers(...args),
  useCover: (...args: unknown[]) => mockUseCover(...args),
  useGenerateCover: (...args: unknown[]) => mockUseGenerateCover(...args),
  useDeleteCover: (...args: unknown[]) => mockUseDeleteCover(...args),
  useCoverTemplates: (...args: unknown[]) => mockUseCoverTemplates(...args),
  useGenerateVariations: jest.fn(() => ({
    mutateAsync: jest.fn(),
    isPending: false,
  })),
}));

// Mock CoverGallery component
jest.mock("@/modules/cover-design/components/CoverGallery", () => ({
  CoverGallery: ({
    covers,
    isLoading,
    emptyMessage,
  }: {
    covers: unknown[];
    isLoading: boolean;
    emptyMessage: string;
  }) => (
    <div data-testid="cover-gallery">
      {isLoading ? (
        <span data-testid="gallery-loading">Loading...</span>
      ) : covers.length > 0 ? (
        <div>
          {covers.map((cover: { id: string; title: string }) => (
            <div key={cover.id} data-testid={`cover-${cover.id}`}>
              {cover.title}
            </div>
          ))}
        </div>
      ) : (
        <div data-testid="gallery-empty">{emptyMessage}</div>
      )}
    </div>
  ),
}));

// Mock CoverGenerator component
jest.mock("@/modules/cover-design/components/CoverGenerator", () => ({
  CoverGenerator: ({ onSuccess }: { onSuccess?: (id: string) => void }) => (
    <div data-testid="cover-generator">
      <span>Generate Cover Form</span>
      <button
        data-testid="generate-submit"
        onClick={() => onSuccess && onSuccess("new-cover-1")}
      >
        Generate
      </button>
    </div>
  ),
}));

// Mock TemplateSelector component
jest.mock("@/modules/cover-design/components/TemplateSelector", () => ({
  TemplateSelector: ({ onSelectTemplate }: { onSelectTemplate?: (template: unknown) => void }) => (
    <div data-testid="template-selector">
      <span>Template Browser</span>
    </div>
  ),
}));

// Mock CoverPreview component
jest.mock("@/modules/cover-design/components/CoverPreview", () => ({
  CoverPreview: ({ cover }: { cover: { title: string } }) => (
    <div data-testid="cover-preview">
      <span>{cover.title}</span>
    </div>
  ),
}));

// Mock Skeleton
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={`animate-pulse ${className || ""}`} />
  ),
}));

// Mock ConfirmDialog
jest.mock("@/components/shared/confirm-dialog", () => ({
  ConfirmDialog: ({
    open,
    onConfirm,
    onCancel,
  }: {
    open: boolean;
    onConfirm: () => void;
    onCancel: () => void;
  }) =>
    open ? (
      <div data-testid="confirm-dialog">
        <button data-testid="confirm-btn" onClick={onConfirm}>
          Confirm
        </button>
        <button data-testid="cancel-btn" onClick={onCancel}>
          Cancel
        </button>
      </div>
    ) : null,
}));

// Import after mocks
import CoverDesignPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockCovers = [
  {
    id: "cover-1",
    org_id: "org-1",
    book_id: null,
    title: "The Dark Forest",
    subtitle: "A Sci-Fi Mystery",
    author_name: "Jane Doe",
    genre: "sci-fi" as const,
    status: "completed" as const,
    image_url: "https://example.com/cover1.png",
    thumbnail_url: "https://example.com/cover1-thumb.png",
    prompt_used: "Dark, futuristic forest scene",
    dimensions: { width_px: 1600, height_px: 2400, dpi: 300, bleed_px: 0 },
    platform: "amazon-kdp" as const,
    metadata: {},
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
  {
    id: "cover-2",
    org_id: "org-1",
    book_id: null,
    title: "Love in Paris",
    subtitle: null,
    author_name: "John Smith",
    genre: "romance" as const,
    status: "completed" as const,
    image_url: "https://example.com/cover2.png",
    thumbnail_url: "https://example.com/cover2-thumb.png",
    prompt_used: "Romantic Eiffel Tower sunset",
    dimensions: { width_px: 1600, height_px: 2400, dpi: 300, bleed_px: 0 },
    platform: "amazon-kdp" as const,
    metadata: {},
    created_at: "2025-05-15T00:00:00Z",
    updated_at: "2025-05-15T00:00:00Z",
  },
];

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: {
  covers?: unknown[];
  coversLoading?: boolean;
  cover?: unknown;
  coverLoading?: boolean;
}) {
  mockUseCovers.mockReturnValue({
    data: overrides?.covers ?? mockCovers,
    isPending: overrides?.coversLoading ?? false,
  });

  mockUseCover.mockReturnValue({
    data: overrides?.cover ?? mockCovers[0],
    isPending: overrides?.coverLoading ?? false,
  });

  mockUseGenerateCover.mockReturnValue({
    mutateAsync: jest.fn().mockResolvedValue({ id: "new-cover-1" }),
    isPending: false,
    isError: false,
  });

  mockUseDeleteCover.mockReturnValue({
    mutateAsync: jest.fn().mockResolvedValue(undefined),
    isPending: false,
  });

  mockUseCoverTemplates.mockReturnValue({
    data: [],
    isPending: false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("CoverDesignPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
  });

  it("renders the Cover Design Studio page with heading", () => {
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByText("Cover Design Studio")).toBeInTheDocument();
  });

  it("renders Generate Cover button", () => {
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByText("Generate Cover")).toBeInTheDocument();
  });

  it("renders cover gallery component", () => {
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("cover-gallery")).toBeInTheDocument();
  });

  it("displays covers when available", () => {
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("cover-cover-1")).toBeInTheDocument();
    expect(screen.getByTestId("cover-cover-2")).toBeInTheDocument();
    expect(screen.getByText("The Dark Forest")).toBeInTheDocument();
    expect(screen.getByText("Love in Paris")).toBeInTheDocument();
  });

  it("shows empty state when no covers exist", () => {
    setDefaultMocks({ covers: [] });
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("gallery-empty")).toBeInTheDocument();
    expect(
      screen.getByText(/No covers yet. Click 'Generate Cover'/i)
    ).toBeInTheDocument();
  });

  it("shows loading state when covers are loading", () => {
    setDefaultMocks({ coversLoading: true });
    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("gallery-loading")).toBeInTheDocument();
  });

  it("navigates to new cover page when Generate Cover button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    const generateBtn = screen.getByText("Generate Cover");
    await user.click(generateBtn);

    expect(mockPush).toHaveBeenCalledWith("/cover-design/new");
  });

  it("renders description text", () => {
    setDefaultMocks();
    renderWithProviders(<CoverDesignPage />);

    expect(
      screen.getByText(/Create stunning book covers with AI-powered design/i)
    ).toBeInTheDocument();
  });
});
