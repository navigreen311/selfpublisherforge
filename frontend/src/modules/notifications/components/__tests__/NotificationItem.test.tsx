import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NotificationItem } from "../NotificationItem";
import type { Notification } from "../../types";
import * as hooks from "../../hooks";

// Mock the hooks
jest.mock("../../hooks", () => ({
  useMarkAsRead: jest.fn(),
}));

describe("NotificationItem", () => {
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

  const mockNotification: Notification = {
    id: "notif-1",
    org_id: "org-1",
    user_id: "user-1",
    type: "info",
    title: "Test Notification",
    message: "This is a test message",
    data: null,
    read_at: null,
    created_at: new Date().toISOString(),
  };

  const mockMarkAsRead = {
    mutate: jest.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (hooks.useMarkAsRead as jest.Mock).mockReturnValue(mockMarkAsRead);
  });

  it("renders notification title and message", () => {
    render(<NotificationItem notification={mockNotification} />, {
      wrapper: createWrapper(),
    });
    expect(screen.getByText("Test Notification")).toBeInTheDocument();
    expect(screen.getByText("This is a test message")).toBeInTheDocument();
  });

  it("shows unread indicator for unread notification", () => {
    const { container } = render(<NotificationItem notification={mockNotification} />, {
      wrapper: createWrapper(),
    });
    const unreadDot = container.querySelector(".bg-blue-600.rounded-full");
    expect(unreadDot).toBeInTheDocument();
  });

  it("does not show unread indicator for read notification", () => {
    const readNotification = {
      ...mockNotification,
      read_at: new Date().toISOString(),
    };
    const { container } = render(<NotificationItem notification={readNotification} />, {
      wrapper: createWrapper(),
    });
    const unreadDot = container.querySelector(".bg-blue-600.rounded-full");
    expect(unreadDot).not.toBeInTheDocument();
  });

  it("calls markAsRead when clicking unread notification", async () => {
    render(<NotificationItem notification={mockNotification} />, {
      wrapper: createWrapper(),
    });
    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockMarkAsRead.mutate).toHaveBeenCalledWith("notif-1");
    });
  });

  it("does not call markAsRead when clicking read notification", async () => {
    const readNotification = {
      ...mockNotification,
      read_at: new Date().toISOString(),
    };
    render(<NotificationItem notification={readNotification} />, {
      wrapper: createWrapper(),
    });
    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockMarkAsRead.mutate).not.toHaveBeenCalled();
    });
  });

  it("calls onClick callback when provided", () => {
    const onClick = jest.fn();
    render(
      <NotificationItem notification={mockNotification} onClick={onClick} />,
      { wrapper: createWrapper() }
    );
    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalled();
  });

  it("displays time ago", () => {
    render(<NotificationItem notification={mockNotification} />, {
      wrapper: createWrapper(),
    });
    // Should show "less than a minute ago" or similar
    expect(screen.getByText(/ago/)).toBeInTheDocument();
  });

  it("renders success icon for success notification", () => {
    const successNotification = {
      ...mockNotification,
      type: "success" as const,
    };
    const { container } = render(<NotificationItem notification={successNotification} />, {
      wrapper: createWrapper(),
    });
    const icon = container.querySelector(".text-green-600");
    expect(icon).toBeInTheDocument();
  });

  it("renders warning icon for warning notification", () => {
    const warningNotification = {
      ...mockNotification,
      type: "warning" as const,
    };
    const { container } = render(<NotificationItem notification={warningNotification} />, {
      wrapper: createWrapper(),
    });
    const icon = container.querySelector(".text-yellow-600");
    expect(icon).toBeInTheDocument();
  });

  it("renders error icon for error notification", () => {
    const errorNotification = {
      ...mockNotification,
      type: "error" as const,
    };
    const { container } = render(<NotificationItem notification={errorNotification} />, {
      wrapper: createWrapper(),
    });
    const icon = container.querySelector(".text-red-600");
    expect(icon).toBeInTheDocument();
  });
});
