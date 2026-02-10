import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Skeleton, PageSkeleton, TableSkeleton } from "../skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse and bg-muted classes", () => {
    const { container } = render(<Skeleton />);
    const skeleton = container.firstElementChild;

    expect(skeleton).toHaveClass("animate-pulse");
    expect(skeleton).toHaveClass("rounded-md");
    expect(skeleton).toHaveClass("bg-muted");
  });

  it("applies custom className", () => {
    const { container } = render(<Skeleton className="h-8 w-48" />);
    const skeleton = container.firstElementChild;

    expect(skeleton).toHaveClass("h-8");
    expect(skeleton).toHaveClass("w-48");
    expect(skeleton).toHaveClass("animate-pulse");
  });

  it("passes through HTML attributes", () => {
    const { container } = render(
      <Skeleton data-testid="test-skeleton" role="progressbar" />
    );
    const skeleton = container.firstElementChild;

    expect(skeleton).toHaveAttribute("data-testid", "test-skeleton");
    expect(skeleton).toHaveAttribute("role", "progressbar");
  });

  it("renders as a div element", () => {
    const { container } = render(<Skeleton />);
    const skeleton = container.firstElementChild;

    expect(skeleton?.tagName).toBe("DIV");
  });
});

describe("PageSkeleton", () => {
  it("renders the outer container with spacing", () => {
    const { container } = render(<PageSkeleton />);
    const wrapper = container.firstElementChild;

    expect(wrapper).toHaveClass("space-y-6", "p-6");
  });

  it("renders multiple skeleton elements", () => {
    const { container } = render(<PageSkeleton />);
    const skeletons = container.querySelectorAll(".animate-pulse");

    // Should have: 1 header skeleton + 3 grid items + 1 large content skeleton = 5
    expect(skeletons.length).toBe(5);
  });

  it("renders a title skeleton with correct dimensions", () => {
    const { container } = render(<PageSkeleton />);
    const titleSkeleton = container.querySelector(".h-8.w-48");

    expect(titleSkeleton).toBeInTheDocument();
    expect(titleSkeleton).toHaveClass("animate-pulse");
  });

  it("renders a grid with 3 card skeletons", () => {
    const { container } = render(<PageSkeleton />);
    const grid = container.querySelector(".grid");

    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-1", "md:grid-cols-3");

    const gridSkeletons = grid?.querySelectorAll(".animate-pulse");
    expect(gridSkeletons?.length).toBe(3);
  });

  it("renders a large content area skeleton", () => {
    const { container } = render(<PageSkeleton />);
    const largeArea = container.querySelector(".h-64");

    expect(largeArea).toBeInTheDocument();
    expect(largeArea).toHaveClass("animate-pulse");
  });
});

describe("TableSkeleton", () => {
  it("renders with default 5 rows", () => {
    const { container } = render(<TableSkeleton />);
    const skeletons = container.querySelectorAll(".animate-pulse");

    // 1 header row + 5 data rows = 6
    expect(skeletons.length).toBe(6);
  });

  it("renders with custom row count", () => {
    const { container } = render(<TableSkeleton rows={3} />);
    const skeletons = container.querySelectorAll(".animate-pulse");

    // 1 header row + 3 data rows = 4
    expect(skeletons.length).toBe(4);
  });

  it("renders with 0 rows (header only)", () => {
    const { container } = render(<TableSkeleton rows={0} />);
    const skeletons = container.querySelectorAll(".animate-pulse");

    // 1 header row + 0 data rows = 1
    expect(skeletons.length).toBe(1);
  });

  it("renders the header skeleton with correct dimensions", () => {
    const { container } = render(<TableSkeleton />);
    const headerSkeleton = container.querySelector(".h-10.w-full");

    expect(headerSkeleton).toBeInTheDocument();
    expect(headerSkeleton).toHaveClass("animate-pulse");
  });

  it("renders row skeletons with correct dimensions", () => {
    const { container } = render(<TableSkeleton rows={2} />);
    const rowSkeletons = container.querySelectorAll(".h-12.w-full");

    expect(rowSkeletons.length).toBe(2);
    rowSkeletons.forEach((row) => {
      expect(row).toHaveClass("animate-pulse");
    });
  });

  it("renders with spacing between rows", () => {
    const { container } = render(<TableSkeleton />);
    const wrapper = container.firstElementChild;

    expect(wrapper).toHaveClass("space-y-3");
  });

  it("renders with 10 custom rows", () => {
    const { container } = render(<TableSkeleton rows={10} />);
    const skeletons = container.querySelectorAll(".animate-pulse");

    // 1 header + 10 rows = 11
    expect(skeletons.length).toBe(11);
  });
});
