import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  Inbox: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="inbox-icon" {...props} />
  ),
}));

// Mock Radix UI Slot so Button renders correctly
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

import { EmptyState } from "../empty-state";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("EmptyState", () => {
  it("renders with all props", () => {
    const onAction = jest.fn();
    render(
      <EmptyState
        title="No projects"
        description="Create your first project to get started."
        actionLabel="Create Project"
        onAction={onAction}
      />
    );

    expect(screen.getByText("No projects")).toBeInTheDocument();
    expect(
      screen.getByText("Create your first project to get started.")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create project/i })
    ).toBeInTheDocument();
  });

  it("renders with only required title prop", () => {
    render(<EmptyState title="Nothing here" />);

    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    // Description should not be rendered
    const paragraphs = document.querySelectorAll("p");
    expect(paragraphs.length).toBe(0);
    // Action button should not be rendered
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders default Inbox icon when no icon is provided", () => {
    render(<EmptyState title="Empty" />);

    expect(screen.getByTestId("inbox-icon")).toBeInTheDocument();
  });

  it("renders a custom icon when provided", () => {
    const CustomIcon = (props: React.SVGAttributes<SVGElement>) => (
      <svg data-testid="custom-icon" {...props} />
    );
    render(
      <EmptyState
        icon={CustomIcon as unknown as import("lucide-react").LucideIcon}
        title="Custom"
      />
    );

    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
    expect(screen.queryByTestId("inbox-icon")).not.toBeInTheDocument();
  });

  it("fires onAction callback when action button is clicked", async () => {
    const onAction = jest.fn();
    render(
      <EmptyState
        title="No items"
        actionLabel="Add Item"
        onAction={onAction}
      />
    );

    const button = screen.getByRole("button", { name: /add item/i });
    await userEvent.click(button);

    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("does not render action button when actionLabel is missing", () => {
    render(
      <EmptyState title="No items" onAction={jest.fn()} />
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not render action button when onAction is missing", () => {
    render(
      <EmptyState title="No items" actionLabel="Add Item" />
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not render description paragraph when description is omitted", () => {
    render(<EmptyState title="Empty" />);

    // Only the title h3 should exist, no <p> for description
    expect(screen.getByText("Empty").tagName).toBe("H3");
    const paragraphs = document.querySelectorAll("p");
    expect(paragraphs.length).toBe(0);
  });

  it("renders the title as an h3 heading", () => {
    render(<EmptyState title="Test Title" />);

    const heading = screen.getByText("Test Title");
    expect(heading.tagName).toBe("H3");
    expect(heading).toHaveClass("text-lg", "font-semibold");
  });
});
