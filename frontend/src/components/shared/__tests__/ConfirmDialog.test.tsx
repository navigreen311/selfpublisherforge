import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { ConfirmDialog } from "../confirm-dialog";

// ── Mock lucide-react ────────────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-loader" {...props} />
  ),
}));

// ── Tests ────────────────────────────────────────────────────────────────

describe("ConfirmDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    onConfirm: jest.fn(),
    title: "Delete item",
    description: "Are you sure you want to delete this item?",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders when open is true", () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByText("Delete item")).toBeInTheDocument();
    expect(
      screen.getByText("Are you sure you want to delete this item?")
    ).toBeInTheDocument();
  });

  it("does not render when open is false", () => {
    render(<ConfirmDialog {...defaultProps} open={false} />);

    expect(screen.queryByText("Delete item")).not.toBeInTheDocument();
  });

  it("renders title and description", () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByText("Delete item")).toBeInTheDocument();
    expect(
      screen.getByText("Are you sure you want to delete this item?")
    ).toBeInTheDocument();
  });

  it("renders default confirm and cancel buttons", () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("renders custom confirmText", () => {
    render(<ConfirmDialog {...defaultProps} confirmText="Yes, delete" />);

    expect(
      screen.getByRole("button", { name: "Yes, delete" })
    ).toBeInTheDocument();
  });

  it("renders custom cancelText", () => {
    render(<ConfirmDialog {...defaultProps} cancelText="No, keep it" />);

    expect(
      screen.getByRole("button", { name: "No, keep it" })
    ).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button is clicked", async () => {
    const user = userEvent.setup();
    const onConfirm = jest.fn();

    render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />);

    const confirmButton = screen.getByRole("button", { name: "Delete" });
    await user.click(confirmButton);

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenChange with false when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onOpenChange = jest.fn();

    render(<ConfirmDialog {...defaultProps} onOpenChange={onOpenChange} />);

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await user.click(cancelButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls legacy onCancel when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onCancel = jest.fn();

    render(<ConfirmDialog {...defaultProps} onCancel={onCancel} />);

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("renders destructive variant button", () => {
    render(<ConfirmDialog {...defaultProps} variant="destructive" />);

    const confirmButton = screen.getByRole("button", { name: "Delete" });
    // Button should exist (variant affects styling, not presence)
    expect(confirmButton).toBeInTheDocument();
  });

  it("renders default variant button", () => {
    render(<ConfirmDialog {...defaultProps} variant="default" />);

    const confirmButton = screen.getByRole("button", { name: "Delete" });
    expect(confirmButton).toBeInTheDocument();
  });

  it("shows loading state when loading is true", () => {
    render(<ConfirmDialog {...defaultProps} loading={true} />);

    expect(screen.getByTestId("icon-loader")).toBeInTheDocument();
    expect(screen.getByText("Processing...")).toBeInTheDocument();
  });

  it("disables buttons when loading", () => {
    render(<ConfirmDialog {...defaultProps} loading={true} />);

    const confirmButton = screen.getByRole("button", { name: "Processing..." });
    const cancelButton = screen.getByRole("button", { name: "Cancel" });

    expect(confirmButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
  });

  it("does not show loading spinner when loading is false", () => {
    render(<ConfirmDialog {...defaultProps} loading={false} />);

    expect(screen.queryByTestId("icon-loader")).not.toBeInTheDocument();
    expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
  });

  it("supports legacy confirmLabel prop", () => {
    render(<ConfirmDialog {...defaultProps} confirmLabel="Confirm Action" />);

    expect(
      screen.getByRole("button", { name: "Confirm Action" })
    ).toBeInTheDocument();
  });

  it("supports legacy cancelLabel prop", () => {
    render(<ConfirmDialog {...defaultProps} cancelLabel="Dismiss" />);

    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
  });

  it("prefers confirmText over legacy confirmLabel", () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmText="New Text"
        confirmLabel="Old Text"
      />
    );

    expect(screen.getByRole("button", { name: "New Text" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Old Text" })
    ).not.toBeInTheDocument();
  });

  it("prefers cancelText over legacy cancelLabel", () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        cancelText="New Cancel"
        cancelLabel="Old Cancel"
      />
    );

    expect(
      screen.getByRole("button", { name: "New Cancel" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Old Cancel" })
    ).not.toBeInTheDocument();
  });

  it("prevents confirm action when loading", async () => {
    const user = userEvent.setup();
    const onConfirm = jest.fn();

    render(
      <ConfirmDialog {...defaultProps} onConfirm={onConfirm} loading={true} />
    );

    const confirmButton = screen.getByRole("button", { name: "Processing..." });
    await user.click(confirmButton);

    // Disabled buttons should not trigger action
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("prevents cancel action when loading", async () => {
    const user = userEvent.setup();
    const onOpenChange = jest.fn();

    render(
      <ConfirmDialog
        {...defaultProps}
        onOpenChange={onOpenChange}
        loading={true}
      />
    );

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await user.click(cancelButton);

    // Disabled buttons should not trigger action
    expect(onOpenChange).not.toHaveBeenCalled();
  });

  it("renders with custom title and description", () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        title="Archive Project"
        description="This will move the project to your archive. You can restore it later."
      />
    );

    expect(screen.getByText("Archive Project")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This will move the project to your archive. You can restore it later."
      )
    ).toBeInTheDocument();
  });
});
