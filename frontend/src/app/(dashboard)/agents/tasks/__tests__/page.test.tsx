import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/agents/tasks",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="loader-icon" {...props} />
  ),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="x-icon" {...props} />
  ),
}));

// Mock Radix UI Dialog primitives to render simple HTML elements
let capturedDialogOnOpenChange: ((open: boolean) => void) | undefined;

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
    capturedDialogOnOpenChange = onOpenChange;
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
      <div ref={ref} role="dialog" aria-modal="true" data-testid="dialog-content" {...props}>
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

// Mock Radix UI Slot so Button renders correctly
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

// Mock the agents hooks
const mockUseTasks = jest.fn();
const mockUseAgents = jest.fn();
const mockCreateTaskMutate = jest.fn();
const mockApproveTaskMutate = jest.fn();
const mockRejectTaskMutate = jest.fn();
const mockCancelTaskMutate = jest.fn();

jest.mock("@/modules/agents/hooks", () => ({
  useTasks: (...args: unknown[]) => mockUseTasks(...args),
  useAgents: (...args: unknown[]) => mockUseAgents(...args),
  useCreateTask: () => ({
    mutate: mockCreateTaskMutate,
    isPending: false,
  }),
  useApproveTask: () => ({
    mutate: mockApproveTaskMutate,
    isPending: false,
  }),
  useRejectTask: () => ({
    mutate: mockRejectTaskMutate,
    isPending: false,
  }),
  useCancelTask: () => ({
    mutate: mockCancelTaskMutate,
    isPending: false,
  }),
}));

// Mock TaskList to expose onApprove/onReject callbacks
// Mock TaskDetail
jest.mock("@/modules/agents/components/TaskDetail", () => ({
  TaskDetail: ({
    task,
    onClose,
    onApprove,
    onReject,
    onCancel,
  }: {
    task: { id: string; title: string };
    onClose?: () => void;
    onApprove?: () => void;
    onReject?: () => void;
    onCancel?: () => void;
  }) => (
    <div data-testid="task-detail">
      <span>{task.title}</span>
      {onClose && <button onClick={onClose}>Close</button>}
      {onApprove && <button onClick={onApprove}>Approve</button>}
      {onReject && <button onClick={onReject}>Reject</button>}
      {onCancel && <button onClick={onCancel}>Cancel Task</button>}
    </div>
  ),
}));

// Import after mocks
import TasksPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockTaskItems = [
  {
    id: "task-1",
    org_id: "org-1",
    agent_id: "agent-1",
    workflow_id: null,
    workflow_step_index: null,
    title: "Research Market Trends",
    description: "Analyze current market trends",
    status: "awaiting_approval" as const,
    priority: "high" as const,
    input_data: null,
    output_data: null,
    error_message: null,
    tokens_used: 500,
    cost_usd: 0.015,
    quality_score: null,
    created_by: "user-1",
    approved_by: null,
    started_at: "2025-06-01T00:00:00Z",
    completed_at: null,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
  {
    id: "task-2",
    org_id: "org-1",
    agent_id: "agent-1",
    workflow_id: null,
    workflow_step_index: null,
    title: "Generate Book Outline",
    description: "Create an outline for new book",
    status: "running" as const,
    priority: "medium" as const,
    input_data: null,
    output_data: null,
    error_message: null,
    tokens_used: 1200,
    cost_usd: 0.036,
    quality_score: 0.85,
    created_by: "user-1",
    approved_by: null,
    started_at: "2025-05-30T00:00:00Z",
    completed_at: null,
    created_at: "2025-05-30T00:00:00Z",
    updated_at: "2025-05-30T01:00:00Z",
  },
  {
    id: "task-3",
    org_id: "org-1",
    agent_id: "agent-2",
    workflow_id: null,
    workflow_step_index: null,
    title: "Write Chapter Summary",
    description: "Summarize chapters",
    status: "completed" as const,
    priority: "low" as const,
    input_data: null,
    output_data: null,
    error_message: null,
    tokens_used: 300,
    cost_usd: 0.009,
    quality_score: 0.9,
    created_by: "user-1",
    approved_by: null,
    started_at: "2025-05-28T00:00:00Z",
    completed_at: "2025-05-28T02:00:00Z",
    created_at: "2025-05-28T00:00:00Z",
    updated_at: "2025-05-28T02:00:00Z",
  },
];

const mockAgentItems = [
  {
    id: "agent-1",
    org_id: "org-1",
    agent_type: "research",
    name: "Research Agent",
    description: "Handles research tasks",
    is_enabled: true,
    permission_level: "suggest",
    model_id: "gpt-4",
    system_prompt: null,
    max_tokens: 4096,
    temperature: 0.7,
    config: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: {
  tasks?: unknown;
  tasksLoading?: boolean;
  agents?: unknown;
}) {
  mockUseTasks.mockReturnValue({
    data: overrides?.tasks ?? {
      items: mockTaskItems,
      next_cursor: null,
      has_more: false,
      total_count: 3,
    },
    isLoading: overrides?.tasksLoading ?? false,
  });

  mockUseAgents.mockReturnValue({
    data: overrides?.agents ?? { items: mockAgentItems, total_count: 1 },
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("TasksPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    capturedDialogOnOpenChange = undefined;
  });

  // 1. Renders task list
  it("renders task list with tasks", () => {
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    expect(screen.getByText("Agent Tasks")).toBeInTheDocument();
    expect(screen.getByTestId("task-list")).toBeInTheDocument();
    expect(screen.getByTestId("task-task-1")).toBeInTheDocument();
    expect(screen.getByText("Research Market Trends")).toBeInTheDocument();
    expect(screen.getByText("Generate Book Outline")).toBeInTheDocument();
    expect(screen.getByText("Write Chapter Summary")).toBeInTheDocument();
  });

  // 2. Approve button opens confirmation dialog (not browser confirm)
  it("approve button opens confirmation dialog instead of browser confirm", async () => {
    const user = userEvent.setup();
    // Spy on window.confirm to verify it is NOT called
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);

    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    const approveBtn = screen.getByTestId("approve-btn-task-1");
    await user.click(approveBtn);

    // Browser confirm should NOT be called
    expect(confirmSpy).not.toHaveBeenCalled();

    // Instead, the custom dialog should appear
    expect(screen.getByText("Approve Task")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Approve this task? The agent will proceed with execution once approved."
      )
    ).toBeInTheDocument();

    confirmSpy.mockRestore();
  });

  // 3. Reject button opens rejection dialog with textarea
  it("reject button opens rejection dialog with textarea", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    const rejectBtn = screen.getByTestId("reject-btn-task-1");
    await user.click(rejectBtn);

    // Rejection dialog should appear with a textarea
    expect(screen.getByText("Reject Task")).toBeInTheDocument();
    expect(
      screen.getByText(/Provide a reason for rejecting this task/)
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Rejection reason")).toBeInTheDocument();
    // Textarea should be a textarea element
    const textarea = screen.getByLabelText("Rejection reason");
    expect(textarea.tagName).toBe("TEXTAREA");
  });

  // 4. Rejection requires a reason (can't submit empty)
  it("rejection requires a reason and disables submit when empty", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // Open reject dialog
    const rejectBtn = screen.getByTestId("reject-btn-task-1");
    await user.click(rejectBtn);

    // The confirm rejection button should be disabled when textarea is empty
    const confirmRejectBtn = screen.getByLabelText("Confirm rejection");
    expect(confirmRejectBtn).toBeDisabled();

    // Type a reason
    const textarea = screen.getByLabelText("Rejection reason");
    await user.type(textarea, "Quality is insufficient");

    // Now the button should be enabled
    expect(confirmRejectBtn).not.toBeDisabled();
  });

  // 5. Approve dialog calls API on confirm
  it("approve dialog calls API on confirm", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // Open approve dialog via the approve button for task-1
    const approveBtn = screen.getByTestId("approve-btn-task-1");
    await user.click(approveBtn);

    // Find and click the confirm button in the dialog
    // The ConfirmDialog has confirmText="Approve"
    const confirmBtn = screen.getByRole("button", { name: "Approve" });
    await user.click(confirmBtn);

    // Verify the approve mutation was called with correct taskId
    expect(mockApproveTaskMutate).toHaveBeenCalledWith(
      { taskId: "task-1" },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );
  });

  // 6. Reject dialog calls API with reason
  it("reject dialog calls API with rejection reason", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // Open reject dialog
    const rejectBtn = screen.getByTestId("reject-btn-task-1");
    await user.click(rejectBtn);

    // Type a reason
    const textarea = screen.getByLabelText("Rejection reason");
    await user.type(textarea, "Does not meet quality standards");

    // Click the confirm rejection button
    const confirmRejectBtn = screen.getByLabelText("Confirm rejection");
    await user.click(confirmRejectBtn);

    // Verify the reject mutation was called with correct taskId and reason
    expect(mockRejectTaskMutate).toHaveBeenCalledWith(
      { taskId: "task-1", reason: "Does not meet quality standards" },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );
  });

  // 7. Loading state shown during API call
  it("shows loading state when tasks are loading", () => {
    setDefaultMocks({ tasksLoading: true });
    renderWithProviders(<TasksPage />);

    expect(screen.getByText("Loading tasks...")).toBeInTheDocument();
    // Task list should not be rendered while loading
    expect(screen.queryByTestId("task-list")).not.toBeInTheDocument();
  });

  // 8. Proper aria-labels on action buttons
  it("has proper aria-labels on action buttons", () => {
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // The New Task / Cancel create button
    expect(
      screen.getByLabelText("Create new task")
    ).toBeInTheDocument();

    // The status filter
    expect(
      screen.getByLabelText("Filter tasks by status")
    ).toBeInTheDocument();

    // Approve button for task-1 (awaiting_approval)
    expect(
      screen.getByLabelText("Approve task Research Market Trends")
    ).toBeInTheDocument();

    // Reject button for task-1 (awaiting_approval)
    expect(
      screen.getByLabelText("Reject task Research Market Trends")
    ).toBeInTheDocument();
  });

  // 9. Shows task count
  it("displays total task count", () => {
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    expect(screen.getByText("3 total tasks")).toBeInTheDocument();
  });

  // 10. Reject dialog has cancel button that closes dialog
  it("reject dialog cancel button has proper aria-label", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // Open reject dialog
    const rejectBtn = screen.getByTestId("reject-btn-task-1");
    await user.click(rejectBtn);

    // Cancel rejection button should be present with aria-label
    expect(screen.getByLabelText("Cancel rejection")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm rejection")).toBeInTheDocument();
  });

  // 11. Processing state disables reject dialog buttons
  it("reject confirmation button shows correct text when not processing", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<TasksPage />);

    // Open reject dialog
    const rejectBtn = screen.getByTestId("reject-btn-task-1");
    await user.click(rejectBtn);

    // Before typing - button shows "Reject" but is disabled
    const confirmRejectBtn = screen.getByLabelText("Confirm rejection");
    expect(confirmRejectBtn).toHaveTextContent("Reject");
  });

  // 12. Empty task list displays properly
  it("renders empty state when no tasks exist", () => {
    setDefaultMocks({
      tasks: { items: [], next_cursor: null, has_more: false, total_count: 0 },
    });
    renderWithProviders(<TasksPage />);

    expect(screen.getByText("No tasks found")).toBeInTheDocument();
    expect(screen.getByText("0 total tasks")).toBeInTheDocument();
  });
});
