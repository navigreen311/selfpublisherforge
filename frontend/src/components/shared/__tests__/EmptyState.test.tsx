import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { EmptyState } from "../empty-state";
import { BookOpen, FileText, Inbox } from "lucide-react";

// ── Mock lucide-react icons ──────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Inbox: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-inbox" {...props} />
  ),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-book-open" {...props} />
  ),
  FileText: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-file-text" {...props} />
  ),
}));

// ── Tests ────────────────────────────────────────────────────────────────

describe("EmptyState", () => {
  it("renders with default icon (Inbox)", () => {
    render(<EmptyState title="No items found" />);

    expect(screen.getByTestId("icon-inbox")).toBeInTheDocument();
    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders with custom BookOpen icon", () => {
    render(<EmptyState icon={BookOpen} title="No books yet" />);

    expect(screen.getByTestId("icon-book-open")).toBeInTheDocument();
    expect(screen.getByText("No books yet")).toBeInTheDocument();
  });

  it("renders with custom FileText icon", () => {
    render(<EmptyState icon={FileText} title="No documents" />);

    expect(screen.getByTestId("icon-file-text")).toBeInTheDocument();
    expect(screen.getByText("No documents")).toBeInTheDocument();
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

  it("has proper semantic structure", () => {
    render(
      <EmptyState
        title="No items found"
        description="Create your first item to get started."
        actionLabel="Create Item"
        onAction={jest.fn()}
      />
    );

    // Check for heading
    expect(screen.getByRole("heading", { name: "No items found" })).toBeInTheDocument();

    // Check for button
    expect(screen.getByRole("button", { name: "Create Item" })).toBeInTheDocument();
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

  it("renders all props together correctly with FileText icon", async () => {
    const user = userEvent.setup();
    const mockAction = jest.fn();

    render(
      <EmptyState
        icon={FileText}
        title="No manuscripts"
        description="Start writing your first book to see it here."
        actionLabel="Start Writing"
        onAction={mockAction}
      />
    );

    expect(screen.getByTestId("icon-file-text")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "No manuscripts" })).toBeInTheDocument();
    expect(screen.getByText("Start writing your first book to see it here.")).toBeInTheDocument();

    const button = screen.getByRole("button", { name: "Start Writing" });
    await user.click(button);

    expect(mockAction).toHaveBeenCalledTimes(1);
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
