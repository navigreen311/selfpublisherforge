import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { EmptyState } from "../empty-state";
import { BookOpen, Inbox } from "lucide-react";

// ── Mock lucide-react icons ──────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  Inbox: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-inbox" {...props} />
  ),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-book-open" {...props} />
  ),
}));

// ── Tests ────────────────────────────────────────────────────────────────

describe("EmptyState", () => {
  it("renders with default icon (Inbox)", () => {
    render(<EmptyState title="No items found" />);

    expect(screen.getByTestId("icon-inbox")).toBeInTheDocument();
    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders with custom icon", () => {
    render(<EmptyState icon={BookOpen} title="No books yet" />);

    expect(screen.getByTestId("icon-book-open")).toBeInTheDocument();
    expect(screen.getByText("No books yet")).toBeInTheDocument();
  });

  it("renders title", () => {
    render(<EmptyState title="Empty library" />);

    expect(screen.getByText("Empty library")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(
      <EmptyState
        title="No projects"
        description="Create your first project to get started."
      />
    );

    expect(screen.getByText("No projects")).toBeInTheDocument();
    expect(
      screen.getByText("Create your first project to get started.")
    ).toBeInTheDocument();
  });

  it("does not render description when not provided", () => {
    const { container } = render(<EmptyState title="Empty" />);

    // Only the title paragraph exists, no description paragraph
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs).toHaveLength(0);
  });

  it("renders action button when actionLabel and onAction are provided", () => {
    const handleAction = jest.fn();

    render(
      <EmptyState
        title="No data"
        actionLabel="Add Data"
        onAction={handleAction}
      />
    );

    const button = screen.getByRole("button", { name: "Add Data" });
    expect(button).toBeInTheDocument();
  });

  it("does not render action button when actionLabel is missing", () => {
    const handleAction = jest.fn();

    render(<EmptyState title="No data" onAction={handleAction} />);

    const button = screen.queryByRole("button");
    expect(button).not.toBeInTheDocument();
  });

  it("does not render action button when onAction is missing", () => {
    render(<EmptyState title="No data" actionLabel="Add Data" />);

    const button = screen.queryByRole("button");
    expect(button).not.toBeInTheDocument();
  });

  it("calls onAction when action button is clicked", async () => {
    const user = userEvent.setup();
    const handleAction = jest.fn();

    render(
      <EmptyState
        title="No items"
        actionLabel="Create Item"
        onAction={handleAction}
      />
    );

    const button = screen.getByRole("button", { name: "Create Item" });
    await user.click(button);

    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("renders all parts together", async () => {
    const user = userEvent.setup();
    const handleAction = jest.fn();

    render(
      <EmptyState
        icon={BookOpen}
        title="No books in your library"
        description="Start adding books to build your collection."
        actionLabel="Add Book"
        onAction={handleAction}
      />
    );

    // Icon
    expect(screen.getByTestId("icon-book-open")).toBeInTheDocument();

    // Title
    expect(screen.getByText("No books in your library")).toBeInTheDocument();

    // Description
    expect(
      screen.getByText("Start adding books to build your collection.")
    ).toBeInTheDocument();

    // Action button
    const button = screen.getByRole("button", { name: "Add Book" });
    expect(button).toBeInTheDocument();

    await user.click(button);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("applies correct CSS classes for styling", () => {
    const { container } = render(
      <EmptyState
        title="Empty"
        description="Description here"
        actionLabel="Action"
        onAction={() => {}}
      />
    );

    // Check for expected container classes
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("flex", "flex-col", "items-center");
  });
});
