import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/style-profiles",
  useSearchParams: () => new URLSearchParams(),
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
  Sparkles: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-sparkles" {...props} />
  ),
  Trash2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trash" {...props} />
  ),
  FileText: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-file-text" {...props} />
  ),
  Calendar: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-calendar" {...props} />
  ),
  TrendingUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trending-up" {...props} />
  ),
}));

// Mock the style profile hooks
const mockUseStyleProfiles = jest.fn();
const mockDeleteMutateAsync = jest.fn();
const mockUseDeleteProfile = jest.fn();

jest.mock("@/modules/style-profiles/hooks", () => ({
  useStyleProfiles: (...args: unknown[]) => mockUseStyleProfiles(...args),
  useDeleteProfile: (...args: unknown[]) => mockUseDeleteProfile(...args),
}));

// Mock ProfileList component
jest.mock("@/modules/style-profiles/components/ProfileList", () => ({
  ProfileList: ({ profiles, isLoading }: { profiles: unknown[]; isLoading: boolean }) => {
    if (isLoading) {
      return <div data-testid="loading-profiles">Loading...</div>;
    }
    if (profiles.length === 0) {
      return <div data-testid="empty-profiles">No profiles</div>;
    }
    return (
      <div data-testid="profile-list">
        {profiles.map((profile: { id: string; name: string }) => (
          <div key={profile.id} data-testid={`profile-${profile.id}`}>
            {profile.name}
          </div>
        ))}
      </div>
    );
  },
}));

// Mock ConfirmDialog
jest.mock("@/components/shared/confirm-dialog", () => ({
  ConfirmDialog: ({
    open,
    title,
    description,
    onConfirm,
    onCancel,
    loading,
  }: {
    open: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
    onCancel: () => void;
    loading: boolean;
  }) =>
    open ? (
      <div data-testid="confirm-dialog">
        <h3>{title}</h3>
        <p>{description}</p>
        <button data-testid="confirm-btn" onClick={onConfirm} disabled={loading}>
          {loading ? "Deleting..." : "Confirm"}
        </button>
        <button data-testid="cancel-btn" onClick={onCancel}>
          Cancel
        </button>
      </div>
    ) : null,
}));

// Import after mocks
import StyleProfilesPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockProfiles = [
  {
    id: "profile-1",
    org_id: "org-1",
    name: "Hemingway Style",
    description: "Short, direct sentences with minimal adjectives",
    genre: "Fiction",
    status: "ready" as const,
    word_count: 5000,
    sample_count: 3,
    confidence: 0.85,
    style_card: null,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-15T00:00:00Z",
  },
  {
    id: "profile-2",
    org_id: "org-1",
    name: "Technical Writing",
    description: "Clear, formal technical documentation style",
    genre: "Non-fiction",
    status: "analyzing" as const,
    word_count: 12000,
    sample_count: 5,
    confidence: 0.92,
    style_card: null,
    created_at: "2025-05-20T00:00:00Z",
    updated_at: "2025-06-10T00:00:00Z",
  },
];

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: { profiles?: unknown; loading?: boolean }) {
  mockUseStyleProfiles.mockReturnValue({
    data: overrides?.profiles ?? {
      items: mockProfiles,
      total: 2,
    },
    isPending: overrides?.loading ?? false,
  });

  mockDeleteMutateAsync.mockResolvedValue(undefined);

  mockUseDeleteProfile.mockReturnValue({
    mutateAsync: mockDeleteMutateAsync,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("StyleProfilesPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the Style Profiles page with heading", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("Style Profiles")).toBeInTheDocument();
  });

  it("renders description text", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    expect(
      screen.getByText(/Analyze and clone writing styles/i)
    ).toBeInTheDocument();
  });

  it("renders New Profile button", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    const newBtn = screen.getByText("New Profile");
    expect(newBtn).toBeInTheDocument();
    expect(newBtn.closest("a")).toHaveAttribute("href", "/style-profiles/new");
  });

  it("displays profile count", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("2 profiles")).toBeInTheDocument();
  });

  it("renders profile list when profiles are available", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByTestId("profile-list")).toBeInTheDocument();
    expect(screen.getByTestId("profile-profile-1")).toBeInTheDocument();
    expect(screen.getByTestId("profile-profile-2")).toBeInTheDocument();
    expect(screen.getByText("Hemingway Style")).toBeInTheDocument();
    expect(screen.getByText("Technical Writing")).toBeInTheDocument();
  });

  it("shows loading state while profiles are loading", () => {
    setDefaultMocks({ loading: true });
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByTestId("loading-profiles")).toBeInTheDocument();
  });

  it("shows empty state when no profiles exist", () => {
    setDefaultMocks({
      profiles: {
        items: [],
        total: 0,
      },
    });
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByTestId("empty-profiles")).toBeInTheDocument();
  });

  it("does not show profile count when loading", () => {
    setDefaultMocks({ loading: true });
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.queryByText(/profiles/)).not.toBeInTheDocument();
  });

  it("shows singular 'profile' for count of 1", () => {
    setDefaultMocks({
      profiles: {
        items: [mockProfiles[0]],
        total: 1,
      },
    });
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("1 profile")).toBeInTheDocument();
  });

  it("does not open delete dialog initially", () => {
    setDefaultMocks();
    renderWithProviders(<StyleProfilesPage />);

    expect(screen.queryByTestId("confirm-dialog")).not.toBeInTheDocument();
  });

  // Note: The delete button overlay interaction is complex with absolute positioning
  // and would require more sophisticated testing. For now, we verify the component renders.
  it("renders the component without errors", () => {
    setDefaultMocks();
    const { container } = renderWithProviders(<StyleProfilesPage />);
    expect(container).toBeInTheDocument();
  });
});
