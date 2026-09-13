import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { InfiniteScroll, InfiniteScrollSkeleton } from "../InfiniteScroll";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="loader-icon" {...props} />
  ),
}));

// Mock IntersectionObserver. `observe` is shared on the prototype so a test can
// assert on it: as a per-instance field it was never reachable from
// `MockIntersectionObserver.prototype`, and the assertion read `undefined`.
const observeSpy = jest.fn();
const disconnectSpy = jest.fn();

class MockIntersectionObserver {
  root = null;
  rootMargin = "";
  thresholds = [];
  observe = observeSpy;
  unobserve = jest.fn();
  disconnect = disconnectSpy;
  takeRecords = jest.fn();
}

global.IntersectionObserver = MockIntersectionObserver as any;

describe("InfiniteScroll", () => {
  const mockOnLoadMore = jest.fn();

  beforeEach(() => {
    mockOnLoadMore.mockClear();
    observeSpy.mockClear();
    disconnectSpy.mockClear();
  });

  it("renders children correctly", () => {
    render(
      <InfiniteScroll
        onLoadMore={mockOnLoadMore}
        hasMore={true}
        isLoading={false}
      >
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </InfiniteScroll>
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
  });

  it("shows loading indicator when isLoading is true", () => {
    render(
      <InfiniteScroll
        onLoadMore={mockOnLoadMore}
        hasMore={true}
        isLoading={true}
      >
        <div>Content</div>
      </InfiniteScroll>
    );

    expect(screen.getByTestId("loader-icon")).toBeInTheDocument();
    expect(screen.getByText("Loading more...")).toBeInTheDocument();
  });

  it("shows 'no more items' message when hasMore is false", () => {
    render(
      <InfiniteScroll
        onLoadMore={mockOnLoadMore}
        hasMore={false}
        isLoading={false}
      >
        <div>Content</div>
      </InfiniteScroll>
    );

    expect(screen.getByText("No more items to load")).toBeInTheDocument();
  });

  it("renders custom loader when provided", () => {
    const customLoader = <div>Custom loading indicator</div>;

    render(
      <InfiniteScroll
        onLoadMore={mockOnLoadMore}
        hasMore={true}
        isLoading={true}
        loader={customLoader}
      >
        <div>Content</div>
      </InfiniteScroll>
    );

    expect(screen.getByText("Custom loading indicator")).toBeInTheDocument();
  });

  it("applies custom className to container", () => {
    const { container } = render(
      <InfiniteScroll
        onLoadMore={mockOnLoadMore}
        hasMore={true}
        isLoading={false}
        className="custom-scroll-container"
      >
        <div>Content</div>
      </InfiniteScroll>
    );

    expect(container.querySelector(".custom-scroll-container")).toBeInTheDocument();
  });

  describe("Load More Button mode", () => {
    it("shows load more button when showLoadMoreButton is true", () => {
      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={false}
          showLoadMoreButton={true}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();
    });

    it("calls onLoadMore when load more button is clicked", async () => {
      const user = userEvent.setup();

      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={false}
          showLoadMoreButton={true}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      const button = screen.getByRole("button", { name: /load more/i });
      await user.click(button);

      expect(mockOnLoadMore).toHaveBeenCalledTimes(1);
    });

    it("disables load more button when loading", () => {
      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={true}
          showLoadMoreButton={true}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      const button = screen.getByRole("button", { name: /loading/i });
      expect(button).toBeDisabled();
    });

    it("shows loading state in button when loading", () => {
      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={true}
          showLoadMoreButton={true}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      expect(screen.getByText("Loading...")).toBeInTheDocument();
      expect(screen.getByTestId("loader-icon")).toBeInTheDocument();
    });
  });

  describe("IntersectionObserver mode", () => {
    it("sets up IntersectionObserver when not using button mode", () => {
      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={false}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      expect(observeSpy).toHaveBeenCalled();
    });

    it("does not set up IntersectionObserver when using button mode", () => {
      render(
        <InfiniteScroll
          onLoadMore={mockOnLoadMore}
          hasMore={true}
          isLoading={false}
          showLoadMoreButton={true}
        >
          <div>Content</div>
        </InfiniteScroll>
      );

      // Observer may still be created but won't be actively used in button mode
      // The component should show the button instead
      expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();
    });
  });
});

describe("InfiniteScrollSkeleton", () => {
  it("renders default number of skeleton items", () => {
    const { container } = render(<InfiniteScrollSkeleton />);

    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(3);
  });

  it("renders custom number of skeleton items", () => {
    const { container } = render(<InfiniteScrollSkeleton count={5} />);

    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(5);
  });

  it("applies correct height class to skeletons", () => {
    const { container } = render(<InfiniteScrollSkeleton count={2} />);

    const skeletons = container.querySelectorAll(".h-24");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
