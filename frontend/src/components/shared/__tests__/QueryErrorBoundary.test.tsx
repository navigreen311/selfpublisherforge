import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryErrorBoundary } from "../QueryErrorBoundary";

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test error from component");
  }
  return <div>No error</div>;
}

describe("QueryErrorBoundary", () => {
  // Suppress console.error for these tests since we're intentionally throwing errors
  const originalError = console.error;
  beforeAll(() => {
    console.error = jest.fn();
  });
  afterAll(() => {
    console.error = originalError;
  });

  it("renders children when there is no error", () => {
    render(
      <QueryErrorBoundary>
        <div>Test content</div>
      </QueryErrorBoundary>
    );

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("renders error UI when child component throws", () => {
    render(
      <QueryErrorBoundary>
        <ThrowError shouldThrow={true} />
      </QueryErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Test error from component")).toBeInTheDocument();
  });

  it("shows Try again button in error state", () => {
    render(
      <QueryErrorBoundary>
        <ThrowError shouldThrow={true} />
      </QueryErrorBoundary>
    );

    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("resets error boundary when Try again is clicked", async () => {
    const user = userEvent.setup();

    // Create a component that tracks render count
    let renderCount = 0;
    function TrackingComponent({ shouldThrow }: { shouldThrow: boolean }) {
      renderCount++;
      if (shouldThrow && renderCount === 1) {
        throw new Error("First render error");
      }
      return <div>Render count: {renderCount}</div>;
    }

    render(
      <QueryErrorBoundary>
        <TrackingComponent shouldThrow={true} />
      </QueryErrorBoundary>
    );

    // Should show error on first render
    expect(screen.getByText("First render error")).toBeInTheDocument();

    // Click try again
    await user.click(screen.getByRole("button", { name: /try again/i }));

    // Should render children again (error was reset)
    expect(screen.getByText(/Render count: 2/)).toBeInTheDocument();
  });

  it("renders custom fallback when provided", () => {
    const customFallback = (error: Error, reset: () => void) => (
      <div>
        <p>Custom error: {error.message}</p>
        <button onClick={reset}>Custom reset</button>
      </div>
    );

    render(
      <QueryErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </QueryErrorBoundary>
    );

    expect(screen.getByText("Custom error: Test error from component")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /custom reset/i })).toBeInTheDocument();
  });

  it("shows default message when error has no message", () => {
    function ThrowEmptyError(): React.JSX.Element {
      throw new Error();
    }

    render(
      <QueryErrorBoundary>
        <ThrowEmptyError />
      </QueryErrorBoundary>
    );

    expect(screen.getByText("An unexpected error occurred while loading this section.")).toBeInTheDocument();
  });

  it("displays error icon", () => {
    render(
      <QueryErrorBoundary>
        <ThrowError shouldThrow={true} />
      </QueryErrorBoundary>
    );

    // The AlertTriangle icon should be present in the error UI
    const heading = screen.getByText("Something went wrong");
    const icon = heading.parentElement?.parentElement?.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });
});
