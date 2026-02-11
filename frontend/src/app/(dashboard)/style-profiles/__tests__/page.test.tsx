import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StyleProfilesPage from "../page";

jest.mock("@/modules/style-profiles/hooks", () => ({
  useStyleProfiles: jest.fn(),
  useDeleteProfile: jest.fn(() => ({
    mutateAsync: jest.fn(),
  })),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

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
}));

jest.mock("@/modules/style-profiles/components/ProfileList", () => ({
  ProfileList: ({ profiles, isLoading }: any) => {
    if (isLoading) return <div data-testid="profile-list-loading">Loading profiles...</div>;
    if (!profiles || profiles.length === 0) return <div data-testid="profile-list-empty">No profiles</div>;
    return <div data-testid="profile-list">{profiles.length} profiles</div>;
  },
}));

jest.mock("@/components/shared/confirm-dialog", () => ({
  ConfirmDialog: ({ open, title, description }: any) => {
    if (!open) return null;
    return (
      <div data-testid="confirm-dialog">
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
    );
  },
}));

import { useStyleProfiles } from "@/modules/style-profiles/hooks";

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("StyleProfilesPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (useStyleProfiles as jest.Mock).mockReturnValue({
      data: { items: [], total: 0 },
      isPending: false,
      error: null,
    });

    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("Style Profiles")).toBeInTheDocument();
  });

  it("shows key elements and description", () => {
    (useStyleProfiles as jest.Mock).mockReturnValue({
      data: { items: [], total: 0 },
      isPending: false,
      error: null,
    });

    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("Style Profiles")).toBeInTheDocument();
    expect(
      screen.getByText(/Analyze and clone writing styles/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /new profile/i })).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useStyleProfiles as jest.Mock).mockReturnValue({
      data: undefined,
      isPending: true,
      error: null,
    });

    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByTestId("profile-list-loading")).toBeInTheDocument();
  });

  it("shows empty state when no profiles exist", () => {
    (useStyleProfiles as jest.Mock).mockReturnValue({
      data: { items: [], total: 0 },
      isPending: false,
      error: null,
    });

    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByText("0 profiles")).toBeInTheDocument();
  });

  it("displays profiles when data is available", () => {
    const mockProfiles = [
      { id: "1", name: "Profile 1" },
      { id: "2", name: "Profile 2" },
    ];

    (useStyleProfiles as jest.Mock).mockReturnValue({
      data: { items: mockProfiles, total: 2 },
      isPending: false,
      error: null,
    });

    renderWithProviders(<StyleProfilesPage />);

    expect(screen.getByTestId("profile-list")).toBeInTheDocument();
    expect(screen.getByText("2 profiles")).toBeInTheDocument();
  });
});
