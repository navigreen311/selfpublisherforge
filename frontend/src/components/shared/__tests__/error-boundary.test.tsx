import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  AlertTriangle: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="alert-triangle-icon" {...props} />
  ),
}));

// Mock Radix UI Slot so that Button renders correctly
jest.mock("@radix-ui/react-slot", () => ({
  Slot: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => {
      if (React.isValidElement(children)) {
        return React.cloneElement(children, {
          ...props,
          ref,
        } as Record<string, unknown>);
      }
      return (
        <div ref={ref} {...props}>
          {children}
        </div>
      );
    }
  ),
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import { ErrorBoundary } from "../error-boundary";

// ─── Helpers ────────────────────────────────────────────────────────────────

// A component that throws an error on render
function ThrowingComponent({ message }: { message: string }) {
  throw new Error(message);
}

// Suppress console.error for expected error boundary catches
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalConsoleError;
});

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("ErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">Hello World</div>
      </ErrorBoundary>
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it('displays "Something went wrong" when a child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="Test error" />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("displays the error message from the thrown error", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="Database connection failed" />
      </ErrorBoundary>
    );

    expect(
      screen.getByText("Database connection failed")
    ).toBeInTheDocument();
  });

  it("displays a default message when error has no message", () => {
    // Component that throws an error without a message
    function ThrowEmpty() {
      throw new Error();
    }

    render(
      <ErrorBoundary>
        <ThrowEmpty />
      </ErrorBoundary>
    );

    // Should fall back to the default text since error.message is empty
    expect(
      screen.getByText("An unexpected error occurred.")
    ).toBeInTheDocument();
  });

  it("renders the AlertTriangle icon", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="Error" />
      </ErrorBoundary>
    );

    expect(screen.getByTestId("alert-triangle-icon")).toBeInTheDocument();
  });

  it('renders a "Try again" button', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="Error" />
      </ErrorBoundary>
    );

    expect(
      screen.getByRole("button", { name: /try again/i })
    ).toBeInTheDocument();
  });

  it('"Try again" button resets error state and re-renders children', async () => {
    let shouldThrow = true;

    function ConditionalThrower() {
      if (shouldThrow) {
        throw new Error("Conditional error");
      }
      return <div data-testid="recovered">Recovered successfully</div>;
    }

    render(
      <ErrorBoundary>
        <ConditionalThrower />
      </ErrorBoundary>
    );

    // Error state should be shown
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Fix the error condition before clicking "Try again"
    shouldThrow = false;

    const tryAgainButton = screen.getByRole("button", { name: /try again/i });
    await userEvent.click(tryAgainButton);

    // Should now render the recovered content
    expect(screen.getByTestId("recovered")).toBeInTheDocument();
    expect(screen.getByText("Recovered successfully")).toBeInTheDocument();
  });

  it("renders custom fallback when provided", () => {
    const fallback = (
      <div data-testid="custom-fallback">Custom error message</div>
    );

    render(
      <ErrorBoundary fallback={fallback}>
        <ThrowingComponent message="Error" />
      </ErrorBoundary>
    );

    expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
    expect(screen.getByText("Custom error message")).toBeInTheDocument();
    // Default UI should NOT be rendered
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("does not show error UI when children render without error", () => {
    render(
      <ErrorBoundary>
        <p>All good</p>
      </ErrorBoundary>
    );

    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /try again/i })
    ).not.toBeInTheDocument();
    expect(screen.getByText("All good")).toBeInTheDocument();
  });
});
