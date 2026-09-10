import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import NotificationSettingsPage from "../page";

// Mock the NotificationPreferences component
// The page renders the settings module's NotificationsTab. Note that this and
// @/modules/notifications/components/NotificationPreferences are two complete
// implementations of the same screen against two different endpoints — see the
// note in the commit that restored this page's heading.
jest.mock("@/modules/settings/components/NotificationsTab", () => ({
  NotificationsTab: () => <div data-testid="notifications-tab">Preferences</div>,
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

  it("renders the notification preferences form", () => {
    render(<NotificationSettingsPage />, { wrapper: createWrapper() });
    expect(screen.getByTestId("notifications-tab")).toBeInTheDocument();
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
