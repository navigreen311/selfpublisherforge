import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="x-icon" {...props} />
  ),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="loader-icon" {...props} />
  ),
}));

// Mock Radix UI Dialog primitives to render simple HTML elements
let capturedOnOpenChange: ((open: boolean) => void) | undefined;

jest.mock("@radix-ui/react-dialog", () => ({
  Root: ({
    children,
    open,
    onOpenChange,
  }: {
    children: React.ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => {
    capturedOnOpenChange = onOpenChange;
    return open ? <div data-testid="dialog-root">{children}</div> : null;
  },
  Portal: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-portal">{children}</div>
  ),
  Overlay: React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    (props, ref) => <div ref={ref} data-testid="dialog-overlay" {...props} />
  ),
  Content: React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ children, ...props }, ref) => (
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        data-testid="dialog-content"
        onKeyDown={(e: React.KeyboardEvent<HTMLDivElement>) => {
          if (e.key === "Escape" && capturedOnOpenChange) {
            capturedOnOpenChange(false);
          }
        }}
        {...props}
      >
        {children}
      </div>
    )
  ),
  Title: React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
    ({ children, ...props }, ref) => (
      <h2 ref={ref} {...props}>
        {children}
      </h2>
    )
  ),
  Description: React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
    ({ children, ...props }, ref) => (
      <p ref={ref} {...props}>
        {children}
      </p>
    )
  ),
  Close: React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
    ({ children, ...props }, ref) => (
      <button ref={ref} {...props}>
        {children}
      </button>
    )
  ),
}));

// Mock Radix UI Slot so that Button renders correctly
jest.mock("@radix-ui/react-slot", () => ({
  // @radix-ui/react-primitive calls createSlot() at module load, so a mock
  // without it throws before any test in the file runs.
  createSlot: () =>
    React.forwardRef(function MockSlot(
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLElement>
    ) {
      return React.isValidElement(children)
        ? React.cloneElement(children, { ...props, ref } as Record<string, unknown>)
        : React.createElement("span", { ref, ...props }, children as React.ReactNode);
    }),
  createSlottable: () =>
    function MockSlottable({ children }: { children?: React.ReactNode }) {
      return children as React.ReactElement;
    },
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

import { ConfirmDialog } from "@/components/shared/confirm-dialog";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("ConfirmDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    title: "Delete Item",
    description: "Are you sure you want to delete this item?",
    onConfirm: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    capturedOnOpenChange = undefined;
  });

  it("renders when open=true", () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("is hidden when open=false", () => {
    render(<ConfirmDialog {...defaultProps} open={false} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows title and description", () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByText("Delete Item")).toBeInTheDocument();
    expect(
      screen.getByText("Are you sure you want to delete this item?")
    ).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", async () => {
    const onConfirm = jest.fn();

    render(
      <ConfirmDialog {...defaultProps} onConfirm={onConfirm} />
    );

    // Default confirm text is "Delete"
    const confirmButton = screen.getByRole("button", { name: "Delete" });
    await userEvent.click(confirmButton);

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenChange(false) when cancel button clicked", async () => {
    const onOpenChange = jest.fn();

    render(
      <ConfirmDialog {...defaultProps} onOpenChange={onOpenChange} />
    );

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await userEvent.click(cancelButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows custom confirmText and cancelText", () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmText="Yes, delete"
        cancelText="No, keep it"
      />
    );

    expect(
      screen.getByRole("button", { name: "Yes, delete" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "No, keep it" })
    ).toBeInTheDocument();
  });

  it("confirm button has destructive styling by default", () => {
    render(<ConfirmDialog {...defaultProps} />);

    // Default variant is "destructive"
    const confirmButton = screen.getByRole("button", { name: "Delete" });
    expect(confirmButton).toHaveClass("bg-destructive");
  });

  it("confirm button has default styling when variant is default", () => {
    render(<ConfirmDialog {...defaultProps} variant="default" />);

    const confirmButton = screen.getByRole("button", { name: "Delete" });
    expect(confirmButton).toHaveClass("bg-primary");
  });

  it("shows loading spinner when loading=true", () => {
    render(<ConfirmDialog {...defaultProps} loading={true} />);

    expect(screen.getByText("Processing...")).toBeInTheDocument();
    expect(screen.getByTestId("loader-icon")).toBeInTheDocument();
  });

  it("confirm button is disabled when loading", () => {
    render(<ConfirmDialog {...defaultProps} loading={true} />);

    const confirmButton = screen.getByRole("button", { name: /Processing/i });
    expect(confirmButton).toBeDisabled();
  });

  it("cancel button is also disabled when loading", () => {
    render(<ConfirmDialog {...defaultProps} loading={true} />);

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    expect(cancelButton).toBeDisabled();
  });

  it("closes on Escape key", () => {
    const onOpenChange = jest.fn();
    render(<ConfirmDialog {...defaultProps} onOpenChange={onOpenChange} />);

    const dialog = screen.getByRole("dialog");
    fireEvent.keyDown(dialog, { key: "Escape", code: "Escape" });

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("has proper role and aria-modal attributes for accessibility", () => {
    render(<ConfirmDialog {...defaultProps} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });
});
