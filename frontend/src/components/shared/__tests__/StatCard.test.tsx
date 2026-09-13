import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StatCard } from "../stat-card";
import { DollarSign, TrendingUp } from "lucide-react";

// ── Mock lucide-react icons ──────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  DollarSign: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-dollar-sign" {...props} />
  ),
  TrendingUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trending-up" {...props} />
  ),
}));

// ── Tests ────────────────────────────────────────────────────────────────

describe("StatCard", () => {
  it("renders label and value", () => {
    render(<StatCard label="Total Revenue" value="$12,450" icon={DollarSign} />);

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$12,450")).toBeInTheDocument();
  });

  it("renders icon", () => {
    render(<StatCard label="Revenue" value="$1000" icon={DollarSign} />);

    expect(screen.getByTestId("icon-dollar-sign")).toBeInTheDocument();
  });

  it("renders numeric value", () => {
    render(<StatCard label="Units Sold" value={1230} icon={TrendingUp} />);

    expect(screen.getByText("Units Sold")).toBeInTheDocument();
    expect(screen.getByText("1230")).toBeInTheDocument();
  });

  it("renders positive trend indicator", () => {
    render(
      <StatCard
        label="Revenue"
        value="$1000"
        icon={DollarSign}
        trend={{ value: 12.5, isPositive: true }}
      />
    );

    const trendText = screen.getByText("+12.5% from last month");
    expect(trendText).toBeInTheDocument();
    expect(trendText).toHaveClass("text-green-600");
  });

  it("renders negative trend indicator", () => {
    render(
      <StatCard
        label="Revenue"
        value="$1000"
        icon={DollarSign}
        trend={{ value: 5.2, isPositive: false }}
      />
    );

    const trendText = screen.getByText("5.2% from last month");
    expect(trendText).toBeInTheDocument();
    expect(trendText).toHaveClass("text-red-600");
  });

  it("does not render trend when not provided", () => {
    render(<StatCard label="Revenue" value="$1000" icon={DollarSign} />);

    expect(screen.queryByText(/from last month/)).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <StatCard
        label="Revenue"
        value="$1000"
        icon={DollarSign}
        className="custom-class"
      />
    );

    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });

  it("renders all parts together with positive trend", () => {
    render(
      <StatCard
        label="Total Revenue"
        value="$12,450.00"
        icon={DollarSign}
        trend={{ value: 12.5, isPositive: true }}
      />
    );

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$12,450.00")).toBeInTheDocument();
    expect(screen.getByTestId("icon-dollar-sign")).toBeInTheDocument();
    expect(screen.getByText("+12.5% from last month")).toBeInTheDocument();
  });

  it("renders all parts together with negative trend", () => {
    render(
      <StatCard
        label="Units Sold"
        value="1,230"
        icon={TrendingUp}
        trend={{ value: 3.2, isPositive: false }}
      />
    );

    expect(screen.getByText("Units Sold")).toBeInTheDocument();
    expect(screen.getByText("1,230")).toBeInTheDocument();
    expect(screen.getByTestId("icon-trending-up")).toBeInTheDocument();
    expect(screen.getByText("3.2% from last month")).toBeInTheDocument();
  });

  it("handles zero trend value", () => {
    render(
      <StatCard
        label="Revenue"
        value="$1000"
        icon={DollarSign}
        trend={{ value: 0, isPositive: true }}
      />
    );

    expect(screen.getByText("+0% from last month")).toBeInTheDocument();
  });

  it("applies correct CSS classes for layout", () => {
    const { container } = render(
      <StatCard
        label="Revenue"
        value="$1000"
        icon={DollarSign}
        trend={{ value: 10, isPositive: true }}
      />
    );

    const card = container.querySelector('[class*="hover:shadow"]');
    expect(card).toBeInTheDocument();
  });

  it("displays very large values correctly", () => {
    render(<StatCard label="Revenue" value="$1,234,567.89" icon={DollarSign} />);

    expect(screen.getByText("$1,234,567.89")).toBeInTheDocument();
  });

  it("displays percentage values correctly", () => {
    render(<StatCard label="Conversion Rate" value="3.5%" icon={TrendingUp} />);

    expect(screen.getByText("3.5%")).toBeInTheDocument();
  });
});
