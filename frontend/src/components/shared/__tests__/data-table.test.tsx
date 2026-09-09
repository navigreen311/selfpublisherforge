import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

jest.mock("lucide-react", () => ({
  ArrowUpDown: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="arrow-up-down-icon" {...props} />
  ),
  ChevronLeft: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-left-icon" {...props} />
  ),
  ChevronRight: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-right-icon" {...props} />
  ),
  Search: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="search-icon" {...props} />
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

// Mock Select components since they use Radix UI primitives
jest.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="select">{children}</div>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="select-content">{children}</div>
  ),
  SelectItem: ({
    children,
    value,
  }: {
    children: React.ReactNode;
    value: string;
  }) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children, ...props }: { children?: React.ReactNode } & Record<string, unknown>) => (
    <button data-testid="select-trigger" {...props}>
      {children}
    </button>
  ),
  SelectValue: () => <span data-testid="select-value" />,
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import { DataTable, DataTableColumn } from "../data-table";

// ─── Helpers ────────────────────────────────────────────────────────────────

interface TestRow {
  id: string;
  name: string;
  age: string;
  [key: string]: unknown;
}

const testColumns: DataTableColumn<TestRow>[] = [
  { key: "id", header: "ID" },
  { key: "name", header: "Name" },
  { key: "age", header: "Age" },
];

const testData: TestRow[] = [
  { id: "1", name: "Alice", age: "30" },
  { id: "2", name: "Bob", age: "25" },
  { id: "3", name: "Charlie", age: "35" },
];

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("DataTable", () => {
  it("renders table with columns and data", () => {
    render(<DataTable columns={testColumns} data={testData} />);

    // Verify all column headers are rendered
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Age")).toBeInTheDocument();

    // Verify all data rows are rendered
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("35")).toBeInTheDocument();
  });

  it("pagination buttons have aria-labels", () => {
    render(<DataTable columns={testColumns} data={testData} />);

    const prevButton = screen.getByRole("button", { name: "Previous page" });
    const nextButton = screen.getByRole("button", { name: "Next page" });

    expect(prevButton).toBeInTheDocument();
    expect(prevButton).toHaveAttribute("aria-label", "Previous page");
    expect(nextButton).toBeInTheDocument();
    expect(nextButton).toHaveAttribute("aria-label", "Next page");
  });

  it("page info displays correctly", () => {
    render(<DataTable columns={testColumns} data={testData} pageSize={10} />);

    // With 3 items and pageSize 10, should show "Page 1 of 1"
    expect(screen.getByText("Page 1 of 1")).toBeInTheDocument();
  });

  it("page info displays correctly with multiple pages", () => {
    // Generate enough data to require multiple pages
    const manyRows: TestRow[] = Array.from({ length: 12 }, (_, i) => ({
      id: String(i + 1),
      name: `User ${i + 1}`,
      age: String(20 + i),
    }));

    render(<DataTable columns={testColumns} data={manyRows} pageSize={5} />);

    // 12 items / 5 per page = 3 pages
    expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
  });

  it("shows empty state when no data is provided", () => {
    render(<DataTable columns={testColumns} data={[]} />);

    expect(screen.getByText("No results found.")).toBeInTheDocument();
  });

  it("shows custom empty message when provided", () => {
    render(
      <DataTable
        columns={testColumns}
        data={[]}
        emptyMessage="Nothing to display."
      />
    );

    expect(screen.getByText("Nothing to display.")).toBeInTheDocument();
  });

  it("does not render pagination when data is empty", () => {
    render(<DataTable columns={testColumns} data={[]} />);

    expect(
      screen.queryByRole("button", { name: "Previous page" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Next page" })
    ).not.toBeInTheDocument();
  });
});
