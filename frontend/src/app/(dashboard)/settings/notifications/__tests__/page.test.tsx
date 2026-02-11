import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import NotificationSettingsPage from "../page";

// Mock the NotificationPreferences component
jest.mock("@/modules/notifications/components/NotificationPreferences", () => ({
  NotificationPreferences: () => <div data-testid="notification-preferences">Preferences</div>,
}));

describe("NotificationSettingsPage", () => {
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

  it("renders the page heading", () => {
    render(<NotificationSettingsPage />, { wrapper: createWrapper() });
    expect(screen.getByText("Notifications")).toBeInTheDocument();
  });

  it("renders the page description", () => {
    render(<NotificationSettingsPage />, { wrapper: createWrapper() });
    expect(
      screen.getByText("Manage how and when you receive notifications.")
    ).toBeInTheDocument();
  });

  it("renders the NotificationPreferences component", () => {
    render(<NotificationSettingsPage />, { wrapper: createWrapper() });
    expect(screen.getByTestId("notification-preferences")).toBeInTheDocument();
  });

  it("has proper heading hierarchy with id for accessibility", () => {
    render(<NotificationSettingsPage />, { wrapper: createWrapper() });
    const heading = screen.getByRole("heading", { name: "Notifications" });
    expect(heading).toHaveAttribute("id", "notification-settings-heading");
  });

  it("has proper section with aria-labelledby", () => {
    const { container } = render(<NotificationSettingsPage />, {
      wrapper: createWrapper(),
    });
    const section = container.querySelector("section");
    expect(section).toHaveAttribute("aria-labelledby", "notification-settings-heading");
  });
});
