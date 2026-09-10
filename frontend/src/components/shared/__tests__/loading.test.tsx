import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Loading } from "../loading";

// Mock lucide-react to avoid SVG rendering issues in jsdom
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="loader-icon" {...props} />
  ),
}));

describe("Loading", () => {
  it("renders without text by default", () => {
    const { container } = render(<Loading />);
    expect(container.querySelector("[data-testid='loader-icon']")).toBeInTheDocument();
    // Should not render any text paragraph
    expect(screen.queryByRole("paragraph")).not.toBeInTheDocument();
  });

  it("renders with loading text when provided", () => {
    render(<Loading text="Loading data..." />);
    expect(screen.getByText("Loading data...")).toBeInTheDocument();
  });

  it("applies default size class", () => {
    const { container } = render(<Loading />);
    const icon = container.querySelector("[data-testid='loader-icon']");
    expect(icon).toHaveClass("h-8", "w-8");
  });

  it("applies sm size class", () => {
    const { container } = render(<Loading size="sm" />);
    const icon = container.querySelector("[data-testid='loader-icon']");
    expect(icon).toHaveClass("h-4", "w-4");
  });

  it("applies lg size class", () => {
    const { container } = render(<Loading size="lg" />);
    const icon = container.querySelector("[data-testid='loader-icon']");
    expect(icon).toHaveClass("h-12", "w-12");
  });

  it("renders with animate-spin class on the icon", () => {
    const { container } = render(<Loading />);
    const icon = container.querySelector("[data-testid='loader-icon']");
    expect(icon).toHaveClass("animate-spin");
  });

  it("renders fullPage variant with min-height wrapper", () => {
    const { container } = render(<Loading fullPage />);
    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass("min-h-[60vh]");
  });

  it("does not render fullPage wrapper by default", () => {
    const { container } = render(<Loading />);
    const wrapper = container.firstElementChild;
    expect(wrapper).not.toHaveClass("min-h-[60vh]");
  });

  it("applies custom className", () => {
    const { container } = render(<Loading className="my-custom-class" />);
    // The custom class should be on the inner flex container
    const flexContainer = container.querySelector(".my-custom-class");
    expect(flexContainer).toBeInTheDocument();
  });
});
