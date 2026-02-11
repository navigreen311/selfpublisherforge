import { render, screen } from "@testing-library/react";
import { NotificationBadge } from "../NotificationBadge";

describe("NotificationBadge", () => {
  it("renders nothing when count is 0", () => {
    const { container } = render(<NotificationBadge count={0} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the count when count is greater than 0", () => {
    render(<NotificationBadge count={5} />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("renders 99+ when count is greater than 99", () => {
    render(<NotificationBadge count={150} />);
    expect(screen.getByText("99+")).toBeInTheDocument();
  });

  it("renders exactly 99 when count is 99", () => {
    render(<NotificationBadge count={99} />);
    expect(screen.getByText("99")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<NotificationBadge count={5} className="custom-class" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("custom-class");
  });
});
