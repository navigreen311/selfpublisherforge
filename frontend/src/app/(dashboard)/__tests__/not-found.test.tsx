import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DashboardNotFound from "../not-found";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe("DashboardNotFound", () => {
  const mockHistoryBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(window, "history", {
      writable: true,
      value: { back: mockHistoryBack },
    });
  });

  it("renders 404 heading", () => {
    render(<DashboardNotFound />);

    expect(screen.getByRole("heading", { name: "404" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Page Not Found" })).toBeInTheDocument();
  });

  it("renders descriptive message", () => {
    render(<DashboardNotFound />);

    expect(
      screen.getByText(/The page you're looking for doesn't exist or has been moved/i)
    ).toBeInTheDocument();
  });

  it("renders Go to Dashboard link with correct href", () => {
    render(<DashboardNotFound />);

    const dashboardLink = screen.getByRole("link", { name: /go to dashboard/i });
    expect(dashboardLink).toHaveAttribute("href", "/dashboard");
  });

  it("renders Go Back button that calls history.back", async () => {
    const user = userEvent.setup();
    render(<DashboardNotFound />);

    const goBackButton = screen.getByRole("button", { name: /go back/i });
    await user.click(goBackButton);

    expect(mockHistoryBack).toHaveBeenCalledTimes(1);
  });

  it("displays file question icon", () => {
    // The icon sits in the card header, above the 404 heading's own section.
    const { container } = render(<DashboardNotFound />);
    expect(container.querySelector("svg[aria-hidden=true]")).toBeInTheDocument();
  });

  it("renders with proper button variants", () => {
    render(<DashboardNotFound />);

    const dashboardLink = screen.getByRole("link", { name: /go to dashboard/i });
    const goBackButton = screen.getByRole("button", { name: /go back/i });

    // Check that both buttons are present and accessible
    expect(dashboardLink).toBeInTheDocument();
    expect(goBackButton).toBeInTheDocument();
  });

  it("has proper semantic HTML structure", () => {
    const { container } = render(<DashboardNotFound />);

    // Should have proper heading hierarchy
    expect(screen.getByRole("heading", { level: 1, name: "404" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Page Not Found" })).toBeInTheDocument();
  });
});
