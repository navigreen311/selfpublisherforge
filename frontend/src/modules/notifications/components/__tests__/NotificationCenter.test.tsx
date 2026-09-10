import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NotificationCenter } from "../NotificationCenter";
import type { Notification } from "../../types";
import * as hooks from "../../hooks";

// Mock the hooks
jest.mock("../../hooks", () => ({
  useNotifications: jest.fn(),
  useUnreadCount: jest.fn(),
  useMarkAllAsRead: jest.fn(),
  useNotificationSubscription: jest.fn(),
  // Each rendered notification row marks itself read on click.
  useMarkAsRead: jest.fn(() => ({
    mutate: jest.fn(),
    mutateAsync: jest.fn().mockResolvedValue({}),
    isPending: false,
    isError: false,
    error: null,
    reset: jest.fn(),
  })),
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

/**
 * The bell is a Radix DropdownMenu trigger, which opens on the full pointer
 * sequence. `fireEvent.click` left it `data-state="closed"`, so every assertion
 * about the panel's contents was reading an unopened menu.
 */
async function openNotifications() {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: /notifications/i }));
  await screen.findByRole("menu");
  return user;
}

describe("NotificationCenter", () => {
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

  const mockNotifications: Notification[] = [
    {
      id: "notif-1",
      org_id: "org-1",
      user_id: "user-1",
      type: "info",
      title: "Test Notification 1",
      message: "Message 1",
      data: null,
      read_at: null,
      created_at: new Date().toISOString(),
    },
    {
      id: "notif-2",
      org_id: "org-1",
      user_id: "user-1",
      type: "success",
      title: "Test Notification 2",
      message: "Message 2",
      data: null,
      read_at: new Date().toISOString(),
      created_at: new Date(Date.now() - 86400000).toISOString(), // Yesterday
    },
  ];

  const mockMarkAllAsRead = {
    mutate: jest.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (hooks.useNotifications as jest.Mock).mockReturnValue({
      data: { items: mockNotifications, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    (hooks.useUnreadCount as jest.Mock).mockReturnValue({
      data: { unread_count: 1 },
    });
    (hooks.useMarkAllAsRead as jest.Mock).mockReturnValue(mockMarkAllAsRead);
    (hooks.useNotificationSubscription as jest.Mock).mockReturnValue(undefined);
  });

  it("renders bell icon button", () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    const button = screen.getByRole("button", { name: /notifications/i });
    expect(button).toBeInTheDocument();
  });

  it("shows unread count badge", () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("does not show badge when unread count is 0", () => {
    (hooks.useUnreadCount as jest.Mock).mockReturnValue({
      data: { unread_count: 0 },
    });
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows loading state when fetching notifications", async () => {
    (hooks.useNotifications as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.getByText("Loading notifications...")).toBeInTheDocument();
  });

  it("shows empty state when no notifications", async () => {
    (hooks.useNotifications as jest.Mock).mockReturnValue({
      data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      isLoading: false,
    });
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.getByText("No notifications yet")).toBeInTheDocument();
  });

  it("displays notifications when opened", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.getByText("Test Notification 1")).toBeInTheDocument();
    expect(screen.getByText("Test Notification 2")).toBeInTheDocument();
  });

  it("groups notifications by Today and Earlier", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Yesterday")).toBeInTheDocument();
  });

  it("shows mark all as read button when there are unread notifications", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.getByText("Mark all read")).toBeInTheDocument();
  });

  it("calls markAllAsRead when clicking mark all as read button", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();

    const markAllButton = screen.getByText("Mark all read");
    fireEvent.click(markAllButton);

    await waitFor(() => {
      expect(mockMarkAllAsRead.mutate).toHaveBeenCalled();
    });
  });

  it("does not show mark all as read button when no unread notifications", async () => {
    (hooks.useUnreadCount as jest.Mock).mockReturnValue({
      data: { unread_count: 0 },
    });
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    expect(screen.queryByText("Mark all read")).not.toBeInTheDocument();
  });

  it("shows settings link", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    // Button asChild + Link renders an anchor, so the role is link.
    const settingsLink = screen.getByRole("link", { name: /notification settings/i });
    expect(settingsLink).toHaveAttribute("href", "/settings/notifications");
  });

  it("shows view all link when there are notifications", async () => {
    render(<NotificationCenter userId="user-1" />, { wrapper: createWrapper() });
    await openNotifications();
    const viewAllLink = screen.getByText("View all notifications");
    expect(viewAllLink.closest("a")).toHaveAttribute("href", "/notifications");
  });

  it("subscribes to notifications for the given user", () => {
    render(<NotificationCenter userId="user-123" />, { wrapper: createWrapper() });
    expect(hooks.useNotificationSubscription).toHaveBeenCalledWith("user-123");
  });
});
