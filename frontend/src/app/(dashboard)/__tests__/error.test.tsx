import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import DashboardError from "../error";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

describe("DashboardError", () => {
  const mockReset = jest.fn();
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it("renders error message", () => {
    const error = new Error("Test error message");
    render(<DashboardError error={error} reset={mockReset} />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("renders default error message when error.message is empty", () => {
    const error = new Error();
    render(<DashboardError error={error} reset={mockReset} />);

    expect(screen.getByText("An unexpected error occurred in this section.")).toBeInTheDocument();
  });

  it("renders error digest when provided", () => {
    const error = Object.assign(new Error("Test error"), { digest: "abc123" });
    render(<DashboardError error={error} reset={mockReset} />);

    expect(screen.getByText(/Error ID: abc123/)).toBeInTheDocument();
  });

  it("calls reset function when Try again button is clicked", async () => {
    const user = userEvent.setup();
    const error = new Error("Test error");
    render(<DashboardError error={error} reset={mockReset} />);

    const tryAgainButton = screen.getByRole("button", { name: /try again/i });
    await user.click(tryAgainButton);

    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("navigates to dashboard when Go to Dashboard button is clicked", async () => {
    const user = userEvent.setup();
    const error = new Error("Test error");
    render(<DashboardError error={error} reset={mockReset} />);

    const goToDashboardButton = screen.getByRole("button", { name: /go to dashboard/i });
    await user.click(goToDashboardButton);

    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("displays error icon", () => {
    const error = new Error("Test error");
    render(<DashboardError error={error} reset={mockReset} />);

    // The AlertTriangle icon should be present
    const icon = screen.getByRole("heading", { name: /something went wrong/i }).parentElement?.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });

  it("renders with proper accessibility attributes", () => {
    const error = new Error("Test error");
    render(<DashboardError error={error} reset={mockReset} />);

    const tryAgainButton = screen.getByRole("button", { name: /try again/i });
    const dashboardButton = screen.getByRole("button", { name: /go to dashboard/i });

    expect(tryAgainButton).toBeEnabled();
    expect(dashboardButton).toBeEnabled();
  });
});
