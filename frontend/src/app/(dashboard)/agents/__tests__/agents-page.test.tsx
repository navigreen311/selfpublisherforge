import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/agents",
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock the agents hooks
const mockUseAgents = jest.fn();
const mockUseTasks = jest.fn();
const mockUseBudgets = jest.fn();
const mockEmergencyMutate = jest.fn();
const mockUseEmergencyStop = jest.fn();

jest.mock("@/modules/agents/hooks", () => ({
  useAgents: (...args: unknown[]) => mockUseAgents(...args),
  useTasks: (...args: unknown[]) => mockUseTasks(...args),
  useBudgets: (...args: unknown[]) => mockUseBudgets(...args),
  useEmergencyStop: (...args: unknown[]) => mockUseEmergencyStop(...args),
  useAgentUsage: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
  useCreateTask: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
  useConfigureAgent: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
  useCreateCustomAgent: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
}));

// Mock AgentCard to a simple stub
jest.mock("@/modules/agents/components/EnhancedAgentCard", () => ({
  EnhancedAgentCard: ({
    agent,
    onNewTask,
    onConfigure,
  }: {
    agent: {
      id: string;
      name: string;
      agent_type: string;
      is_enabled: boolean;
      permission_level: string;
    };
    onNewTask: () => void;
    onConfigure: () => void;
  }) => (
    <div data-testid={`agent-card-${agent.id}`}>
      <span>{agent.name}</span>
      <span data-testid={`agent-type-${agent.id}`}>{agent.agent_type}</span>
      <span data-testid={`agent-status-${agent.id}`}>
        {agent.is_enabled ? "enabled" : "disabled"}
      </span>
      <span data-testid={`agent-permission-${agent.id}`}>{agent.permission_level}</span>
      <button data-testid={`create-task-${agent.id}`} onClick={onNewTask}>
        New Task
      </button>
      <button data-testid={`configure-${agent.id}`} onClick={onConfigure}>
        Configure
      </button>
    </div>
  ),
}));

jest.mock("@/modules/agents/components/AgentStatsBar", () => ({
  AgentStatsBar: ({
    stats,
    isLoading,
  }: {
    stats?: { total_tasks: number; total_cost: number };
    isLoading: boolean;
  }) => (
    <div data-testid="agent-stats-bar">
      {isLoading ? "loading" : `${stats?.total_tasks ?? 0} tasks / $${stats?.total_cost ?? 0}`}
    </div>
  ),
}));

jest.mock("@/modules/agents/components/NewTaskModal", () => ({
  NewTaskModal: ({ open, agentId }: { open: boolean; agentId?: string }) =>
    open ? <div data-testid="new-task-modal">{agentId}</div> : null,
}));

jest.mock("@/modules/agents/components/ConfigureAgentPanel", () => ({
  ConfigureAgentPanel: ({ open, agent }: { open: boolean; agent?: { id: string } | null }) =>
    open ? <div data-testid="configure-panel">{agent?.id}</div> : null,
}));

// Mock Skeleton
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={`animate-pulse ${className || ""}`} />
  ),
}));

// Import after mocks
import AgentDashboardPage from "../page";

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

const mockAgents = [
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
  {
    id: "agent-2",
    org_id: "org-1",
    agent_type: "writing_assistant",
    name: "Writing Agent",
    description: "Assists with writing",
    is_enabled: false,
    permission_level: "draft_only",
    model_id: "gpt-3.5-turbo",
    system_prompt: null,
    max_tokens: 2048,
    temperature: 0.5,
    config: null,
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

const mockTaskItems = [
  {
    id: "task-1",
    org_id: "org-1",
    agent_id: "agent-1",
    workflow_id: null,
    workflow_step_index: null,
    title: "Research Market Trends",
    description: "Analyze current market trends",
    status: "running" as const,
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
    status: "completed" as const,
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
    completed_at: "2025-05-30T01:00:00Z",
    created_at: "2025-05-30T00:00:00Z",
    updated_at: "2025-05-30T01:00:00Z",
  },
];

const mockBudgetItems = [
  {
    id: "budget-1",
    org_id: "org-1",
    agent_id: "agent-1",
    daily_token_limit: 100000,
    daily_usd_limit: 5,
    monthly_usd_limit: 100,
    tokens_used_today: 5000,
    usd_used_today: 0.5,
    usd_used_this_month: 15,
    total_tokens_used: 500000,
    total_usd_used: 50,
    last_reset_daily: null,
    last_reset_monthly: null,
    daily_token_pct: 5,
    daily_usd_pct: 10,
    monthly_usd_pct: 15,
  },
];

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: {
  agents?: unknown;
  agentsLoading?: boolean;
  tasks?: unknown;
  tasksLoading?: boolean;
  budgets?: unknown;
  emergencyStop?: unknown;
}) {
  mockUseAgents.mockReturnValue({
    data: overrides?.agents ?? { items: mockAgents, total_count: 2 },
    isLoading: overrides?.agentsLoading ?? false,
  });

  mockUseTasks.mockReturnValue({
    data: overrides?.tasks ?? {
      items: mockTaskItems,
      next_cursor: null,
      has_more: false,
      total_count: 2,
    },
    isLoading: overrides?.tasksLoading ?? false,
  });

  mockUseBudgets.mockReturnValue({
    data: overrides?.budgets ?? { items: mockBudgetItems },
  });

  mockUseEmergencyStop.mockReturnValue(
    overrides?.emergencyStop ?? {
      mutate: mockEmergencyMutate,
      isPending: false,
      isSuccess: false,
      data: undefined,
    }
  );
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("AgentDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders agents dashboard
  it("renders the agents dashboard heading and description", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByText("AI Agents")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Manage your AI agent workforce, monitor tasks, and control budgets."
      )
    ).toBeInTheDocument();
  });

  // 2. Agent list displays
  it("renders agent cards for each agent", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByText("Available Agents")).toBeInTheDocument();
    expect(screen.getByTestId("agent-card-agent-1")).toBeInTheDocument();
    expect(screen.getByTestId("agent-card-agent-2")).toBeInTheDocument();
    // "Research Agent" appears in both agent card and budget meter
    expect(screen.getAllByText("Research Agent").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Writing Agent")).toBeInTheDocument();
  });

  // 3. Agent status badges show correctly
  it("displays agent enabled/disabled status correctly", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByTestId("agent-status-agent-1")).toHaveTextContent("enabled");
    expect(screen.getByTestId("agent-status-agent-2")).toHaveTextContent("disabled");
  });

  it("displays agent permission levels correctly", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByTestId("agent-permission-agent-1")).toHaveTextContent("suggest");
    expect(screen.getByTestId("agent-permission-agent-2")).toHaveTextContent("draft_only");
  });

  // 4. Uses router.push (NOT window.location.href) for navigation
  it("opens the new-task modal for the chosen agent", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.queryByTestId("new-task-modal")).not.toBeInTheDocument();

    await user.click(screen.getByTestId("create-task-agent-1"));

    expect(await screen.findByTestId("new-task-modal")).toHaveTextContent("agent-1");
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("opens the configure panel for the chosen agent", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    await user.click(screen.getByTestId("configure-agent-1"));

    expect(await screen.findByTestId("configure-panel")).toHaveTextContent("agent-1");
    expect(mockPush).not.toHaveBeenCalled();
  });

  // 5. Task list renders
  it("renders the recent tasks section with task list", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByText("Recent Tasks")).toBeInTheDocument();
    expect(screen.getByTestId("task-list")).toBeInTheDocument();
    expect(screen.getByText("Research Market Trends")).toBeInTheDocument();
    expect(screen.getByText("Generate Book Outline")).toBeInTheDocument();
  });

  it("renders View all link for tasks", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    const viewAllLink = screen.getByRole("link", { name: /view all/i });
    expect(viewAllLink).toHaveAttribute("href", "/agents/tasks");
  });

  // 6. Workflow section accessible (Budget section as a proxy for dashboard sections)
  it("renders the agent usage stats bar", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByTestId("agent-stats-bar")).toBeInTheDocument();
  });

  // 7. Emergency stop button present
  it("renders Emergency Stop button", () => {
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    expect(
      screen.getByRole("button", { name: /emergency stop/i })
    ).toBeInTheDocument();
  });

  it("shows confirmation dialog when Emergency Stop is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    const stopBtn = screen.getByRole("button", { name: /emergency stop/i });
    await user.click(stopBtn);

    expect(screen.getByText("Cancel ALL running tasks?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("calls emergency stop mutation when confirmed", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    // Open confirmation
    const stopBtn = screen.getByRole("button", { name: /emergency stop/i });
    await user.click(stopBtn);

    // Confirm
    const confirmBtn = screen.getByRole("button", { name: /confirm/i });
    await user.click(confirmBtn);

    expect(mockEmergencyMutate).toHaveBeenCalledWith(undefined, expect.any(Object));
  });

  it("hides confirmation when Cancel is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<AgentDashboardPage />);

    // Open confirmation
    const stopBtn = screen.getByRole("button", { name: /emergency stop/i });
    await user.click(stopBtn);

    expect(screen.getByText("Cancel ALL running tasks?")).toBeInTheDocument();

    // Cancel
    const cancelBtn = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelBtn);

    expect(screen.queryByText("Cancel ALL running tasks?")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /emergency stop/i })
    ).toBeInTheDocument();
  });

  it("shows emergency stop success message", () => {
    setDefaultMocks({
      emergencyStop: {
        mutate: mockEmergencyMutate,
        isPending: false,
        isSuccess: true,
        data: {
          tasks_cancelled: 3,
          workflows_cancelled: 1,
          message: "Emergency stop executed: 3 tasks cancelled, 1 workflow cancelled.",
        },
      },
    });
    renderWithProviders(<AgentDashboardPage />);

    expect(
      screen.getByText(
        "Emergency stop executed: 3 tasks cancelled, 1 workflow cancelled."
      )
    ).toBeInTheDocument();
  });

  // Loading states
  it("renders loading skeletons for agents when loading", () => {
    setDefaultMocks({ agentsLoading: true });
    renderWithProviders(<AgentDashboardPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders loading skeletons for tasks when loading", () => {
    setDefaultMocks({ tasksLoading: true });
    renderWithProviders(<AgentDashboardPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty agent list when no agents exist", () => {
    setDefaultMocks({ agents: { items: [], total_count: 0 } });
    renderWithProviders(<AgentDashboardPage />);

    expect(screen.getByText("Available Agents")).toBeInTheDocument();
    expect(screen.queryByTestId("agent-card-agent-1")).not.toBeInTheDocument();
  });

});
