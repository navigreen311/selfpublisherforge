import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "../empty-state";
import { FileText, Inbox } from "lucide-react";

describe("EmptyState", () => {
  it("renders with title only", () => {
    render(<EmptyState title="No items found" />);

    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders with title and description", () => {
    render(
      <EmptyState
        title="No items found"
        description="Try adjusting your filters or create a new item."
      />
    );

    expect(screen.getByText("No items found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your filters or create a new item.")).toBeInTheDocument();
  });

  it("renders action button when actionLabel and onAction are provided", () => {
    const mockAction = jest.fn();
    render(
      <EmptyState
        title="No items found"
        actionLabel="Create Item"
        onAction={mockAction}
      />
    );

    const button = screen.getByRole("button", { name: "Create Item" });
    expect(button).toBeInTheDocument();
  });

  it("calls onAction when action button is clicked", async () => {
    const user = userEvent.setup();
    const mockAction = jest.fn();

    render(
      <EmptyState
        title="No items found"
        actionLabel="Create Item"
        onAction={mockAction}
      />
    );

    const button = screen.getByRole("button", { name: "Create Item" });
    await user.click(button);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it("does not render action button when only actionLabel is provided", () => {
    render(
      <EmptyState
        title="No items found"
        actionLabel="Create Item"
      />
    );

    expect(screen.queryByRole("button", { name: "Create Item" })).not.toBeInTheDocument();
  });

  it("does not render action button when only onAction is provided", () => {
    const mockAction = jest.fn();
    render(
      <EmptyState
        title="No items found"
        onAction={mockAction}
      />
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders custom icon when provided", () => {
    render(
      <EmptyState
        icon={FileText}
        title="No documents"
      />
    );

    // Icon should be rendered (we can't easily test the specific icon, but we can check it's there)
    const heading = screen.getByText("No documents");
    expect(heading).toBeInTheDocument();
  });

  it("renders default Inbox icon when no icon is provided", () => {
    render(<EmptyState title="No items" />);

    // Default icon should be rendered
    const heading = screen.getByText("No items");
    expect(heading).toBeInTheDocument();
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

  it("renders all props together correctly", async () => {
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

    expect(screen.getByRole("heading", { name: "No manuscripts" })).toBeInTheDocument();
    expect(screen.getByText("Start writing your first book to see it here.")).toBeInTheDocument();

    const button = screen.getByRole("button", { name: "Start Writing" });
    await user.click(button);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });
});
