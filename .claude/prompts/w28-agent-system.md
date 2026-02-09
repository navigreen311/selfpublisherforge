# W28: AI Agent System + Governance (Modules #10 + #21)
**Branch:** `ai-feature/agent-system`
**Scope:** fullstack

## Mission
Build the AI Agent Workforce and Governance Layer: agent definitions, task execution, multi-step workflows, permission levels, cost budgets, quality SLAs, audit trail, and emergency stop.

## Agent Types
- Research Agent — market research, competitor analysis, keyword discovery
- Writing Assistant Agent — drafting, continuation, editing suggestions
- Editor Agent — grammar, style, consistency checking
- Marketing Copy Agent — blurbs, ad copy, email sequences, social posts

## Permission Levels
- Draft Only — can only generate drafts, human must approve
- Suggest — can suggest changes, human approves
- Auto-Execute (Low Risk) — can execute low-risk tasks autonomously
- Auto-Execute (High Risk) — can execute any task (requires admin approval to enable)
- Full Autonomous — no human oversight (enterprise only)

## API Endpoints
- GET /api/v1/agents — List available agent types
- GET /api/v1/agents/{id}/config — Get agent configuration
- PATCH /api/v1/agents/{id}/config — Update agent configuration (permissions, model, budget)
- POST /api/v1/agents/tasks — Create agent task
- GET /api/v1/agents/tasks — List tasks (filterable by status, agent, date)
- GET /api/v1/agents/tasks/{id} — Task detail with input/output
- POST /api/v1/agents/tasks/{id}/approve — Approve task output
- POST /api/v1/agents/tasks/{id}/reject — Reject and optionally regenerate
- POST /api/v1/agents/tasks/{id}/cancel — Cancel running task
- POST /api/v1/agents/workflows — Create multi-step workflow
- GET /api/v1/agents/workflows — List workflows
- GET /api/v1/agents/budgets — Get budget status (token/USD/daily)
- PATCH /api/v1/agents/budgets — Update budget limits
- POST /api/v1/agents/emergency-stop — Emergency stop all running tasks
- GET /api/v1/agents/audit — Audit trail (paginated)

## What to Build

### Backend
1. **backend/app/modules/agent_system/__init__.py**
2. **backend/app/modules/agent_system/router.py** — All endpoints
3. **backend/app/modules/agent_system/schemas.py** — Agent, AgentConfig, AgentTask, TaskCreate, TaskResult, Workflow, WorkflowStep, BudgetStatus, AuditEntry
4. **backend/app/modules/agent_system/service.py** — Agent CRUD, task execution orchestration, workflow management
5. **backend/app/modules/agent_system/executor.py** — Task executor: receive task, check permissions, check budget, execute via LLM orchestrator, quality check, record result
6. **backend/app/modules/agent_system/workflow_engine.py** — Multi-step workflow: step execution, conditional branching, error handling, resume
7. **backend/app/modules/agent_system/governance.py** — Permission enforcement, budget checking, quality SLA validation, emergency stop
8. **backend/app/modules/agent_system/audit.py** — Audit trail recording: every agent action logged with actor, resource, details
9. **backend/app/tasks/agent_system.py** — Celery tasks for async agent execution, workflow step execution

### Frontend
10. **frontend/src/app/(dashboard)/agents/page.tsx** — Agent dashboard: active tasks, available agents, budget status
11. **frontend/src/app/(dashboard)/agents/tasks/page.tsx** — Task list with status filters and approval queue
12. **frontend/src/app/(dashboard)/agents/workflows/page.tsx** — Workflow builder and management
13. **frontend/src/app/(dashboard)/agents/settings/page.tsx** — Agent configuration, permissions, budgets
14. **frontend/src/modules/agents/hooks.ts** — React Query hooks + WebSocket for real-time task updates
15. **frontend/src/modules/agents/components/** — AgentCard, TaskList, TaskDetail, WorkflowBuilder, BudgetMeter, AuditLog

### Tests
16. **backend/tests/unit/test_agent_executor.py**
17. **backend/tests/unit/test_governance.py**
18. **backend/tests/integration/test_agent_api.py**

## Database Tables (from W02, read-only)
agents, agent_tasks, agent_workflows, agent_budgets, audit_trail

## Commit Convention
`feat(agents): implement AI agent workforce with governance, budgets, and audit trail`
