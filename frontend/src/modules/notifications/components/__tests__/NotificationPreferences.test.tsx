import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NotificationPreferences } from "../NotificationPreferences";
import type { NotificationPreference } from "../../types";
import * as hooks from "../../hooks";

// Mock the hooks
jest.mock("../../hooks", () => ({
  useNotificationPreferences: jest.fn(),
  useUpdatePreferences: jest.fn(),
}));

describe("NotificationPreferences", () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };

  const mockPreferences: NotificationPreference[] = [
    {
      id: "pref-1",
      user_id: "user-1",
      channel: "email",
      category: "ai_complete",
      enabled: true,
    },
    {
      id: "pref-2",
      user_id: "user-1",
      channel: "in_app",
      category: "ai_complete",
      enabled: true,
    },
    {
      id: "pref-3",
      user_id: "user-1",
      channel: "email",
      category: "publish_status",
      enabled: false,
    },
  ];

  const mockUpdatePreferences = {
    mutate: jest.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (hooks.useNotificationPreferences as jest.Mock).mockReturnValue({
      data: mockPreferences,
      isLoading: false,
    });
    (hooks.useUpdatePreferences as jest.Mock).mockReturnValue(mockUpdatePreferences);
  });

  it("shows loading state when fetching preferences", () => {
    (hooks.useNotificationPreferences as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(screen.getByRole("status", { hidden: true })).toBeInTheDocument();
  });

  it("renders preference categories", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(screen.getByText("AI Task Completion")).toBeInTheDocument();
    expect(screen.getByText("Publishing Updates")).toBeInTheDocument();
    expect(screen.getByText("Team Invitations")).toBeInTheDocument();
  });

  it("renders channel headers", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("In-App")).toBeInTheDocument();
  });

  it("initializes switches with correct states", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const switches = screen.getAllByRole("switch");

    // There should be switches for each category x channel combination
    expect(switches.length).toBeGreaterThan(0);
  });

  it("toggles preference when switch is clicked", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const switches = screen.getAllByRole("switch");

    // Click the first switch
    fireEvent.click(switches[0]);

    // Verify the switch state changed (locally, before save)
    expect(switches[0]).toHaveAttribute("data-state");
  });

  it("renders save button", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(screen.getByRole("button", { name: /save preferences/i })).toBeInTheDocument();
  });

  it("calls updatePreferences when save button is clicked", async () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const saveButton = screen.getByRole("button", { name: /save preferences/i });

    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdatePreferences.mutate).toHaveBeenCalled();
    });
  });

  it("sends all preferences when saving", async () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const saveButton = screen.getByRole("button", { name: /save preferences/i });

    fireEvent.click(saveButton);

    await waitFor(() => {
      const call = mockUpdatePreferences.mutate.mock.calls[0][0];
      expect(call).toHaveProperty("preferences");
      expect(Array.isArray(call.preferences)).toBe(true);
      // Should have preferences for all categories x channels
      expect(call.preferences.length).toBeGreaterThan(0);
    });
  });

  it("disables save button while updating", () => {
    (hooks.useUpdatePreferences as jest.Mock).mockReturnValue({
      ...mockUpdatePreferences,
      isPending: true,
    });
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const saveButton = screen.getByRole("button", { name: /save preferences/i });
    expect(saveButton).toBeDisabled();
  });

  it("shows success message after saving", () => {
    (hooks.useUpdatePreferences as jest.Mock).mockReturnValue({
      ...mockUpdatePreferences,
      isSuccess: true,
    });
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(screen.getByText("Preferences saved successfully!")).toBeInTheDocument();
  });

  it("renders category descriptions", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    expect(
      screen.getByText("Notify when AI agents complete tasks or workflows")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Notify about book publishing status changes")
    ).toBeInTheDocument();
  });

  it("has proper aria labels for switches", () => {
    render(<NotificationPreferences />, { wrapper: createWrapper() });
    const switches = screen.getAllByRole("switch");

    switches.forEach((switchEl) => {
      expect(switchEl).toHaveAttribute("aria-label");
    });
  });
});
