"use client";

import { useState } from "react";
import {
  useAgents,
  useUpdateAgentConfig,
  useBudgets,
  useUpdateBudget,
  useAudit,
} from "@/modules/agents/hooks";
import { BudgetMeter } from "@/modules/agents/components/BudgetMeter";
import { AuditLog } from "@/modules/agents/components/AuditLog";
import type { Agent, AgentConfigUpdate, PermissionLevel } from "@/modules/agents/types";

const PERMISSION_OPTIONS: { value: PermissionLevel; label: string }[] = [
  { value: "draft_only", label: "Draft Only" },
  { value: "suggest", label: "Suggest" },
  { value: "auto_execute_low", label: "Auto-Execute (Low Risk)" },
  { value: "auto_execute_high", label: "Auto-Execute (High Risk)" },
  { value: "full_autonomous", label: "Full Autonomous" },
];

function AgentConfigForm({
  agent,
  onSave,
  isSaving,
}: {
  agent: Agent;
  onSave: (updates: AgentConfigUpdate) => void;
  isSaving: boolean;
}) {
  const [name, setName] = useState(agent.name);
  const [description, setDescription] = useState(agent.description || "");
  const [isEnabled, setIsEnabled] = useState(agent.is_enabled);
  const [permissionLevel, setPermissionLevel] = useState(agent.permission_level);
  const [modelId, setModelId] = useState(agent.model_id);
  const [maxTokens, setMaxTokens] = useState(agent.max_tokens);
  const [temperature, setTemperature] = useState(agent.temperature);
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      name,
      description: description || undefined,
      is_enabled: isEnabled,
      permission_level: permissionLevel,
      model_id: modelId,
      max_tokens: maxTokens,
      temperature,
      system_prompt: systemPrompt || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Permission Level
          </label>
          <select
            value={permissionLevel}
            onChange={(e) =>
              setPermissionLevel(e.target.value as PermissionLevel)
            }
            className="w-full rounded-md border px-3 py-2 text-sm"
          >
            {PERMISSION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Model ID</label>
          <input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Max Tokens</label>
          <input
            type="number"
            min={1}
            max={200000}
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value, 10))}
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Temperature ({temperature.toFixed(1)})
          </label>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="enabled"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="enabled" className="text-sm font-medium">
            Enabled
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full rounded-md border px-3 py-2 text-sm"
          rows={2}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">System Prompt</label>
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          className="w-full rounded-md border px-3 py-2 text-sm font-mono"
          rows={4}
        />
      </div>

      <button
        type="submit"
        disabled={isSaving}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {isSaving ? "Saving..." : "Save Configuration"}
      </button>
    </form>
  );
}

export default function AgentSettingsPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");

  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const updateConfig = useUpdateAgentConfig();
  const { data: budgetsData } = useBudgets();
  const updateBudget = useUpdateBudget();
  const { data: auditData } = useAudit({ limit: 20 });

  const agents = agentsData?.items || [];
  const budgets = budgetsData?.items || [];
  const auditEntries = auditData?.items || [];

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || null;
  const selectedBudget = budgets.find((b) => b.agent_id === selectedAgentId) || null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Agent Settings</h1>
        <p className="text-muted-foreground">
          Configure agent permissions, models, budgets, and view the audit trail.
        </p>
      </div>

      {/* Agent selector */}
      <div>
        <label className="block text-sm font-medium mb-1">Select Agent</label>
        <select
          value={selectedAgentId}
          onChange={(e) => setSelectedAgentId(e.target.value)}
          className="rounded-md border px-3 py-2 text-sm w-full max-w-sm"
        >
          <option value="">Choose an agent...</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.agent_type})
            </option>
          ))}
        </select>
      </div>

      {agentsLoading && (
        <div className="text-muted-foreground">Loading agents...</div>
      )}

      {/* Agent config */}
      {selectedAgent && (
        <section className="space-y-6">
          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">
              Configuration: {selectedAgent.name}
            </h2>
            <AgentConfigForm
              agent={selectedAgent}
              onSave={(updates) =>
                updateConfig.mutate({ agentId: selectedAgent.id, updates })
              }
              isSaving={updateConfig.isPending}
            />
            {updateConfig.isSuccess && (
              <div className="mt-3 rounded-md bg-green-50 p-3 text-sm text-green-700">
                Configuration saved successfully.
              </div>
            )}
          </div>

          {/* Budget */}
          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Budget</h2>
            {selectedBudget ? (
              <div className="space-y-4">
                <BudgetMeter
                  budget={selectedBudget}
                  agentName={selectedAgent.name}
                />
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Daily Token Limit
                    </label>
                    <input
                      type="number"
                      defaultValue={selectedBudget.daily_token_limit}
                      onBlur={(e) =>
                        updateBudget.mutate({
                          agentId: selectedAgent.id,
                          updates: {
                            daily_token_limit: parseInt(e.target.value, 10),
                          },
                        })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Daily USD Limit
                    </label>
                    <input
                      type="number"
                      step={0.01}
                      defaultValue={selectedBudget.daily_usd_limit}
                      onBlur={(e) =>
                        updateBudget.mutate({
                          agentId: selectedAgent.id,
                          updates: {
                            daily_usd_limit: parseFloat(e.target.value),
                          },
                        })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Monthly USD Limit
                    </label>
                    <input
                      type="number"
                      step={0.01}
                      defaultValue={selectedBudget.monthly_usd_limit}
                      onBlur={(e) =>
                        updateBudget.mutate({
                          agentId: selectedAgent.id,
                          updates: {
                            monthly_usd_limit: parseFloat(e.target.value),
                          },
                        })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No budget configured for this agent yet. It will be created
                automatically when the first task runs.
              </p>
            )}
          </div>
        </section>
      )}

      {/* Audit trail */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Audit Trail</h2>
        <AuditLog
          entries={auditEntries}
          hasMore={auditData?.has_more}
        />
      </section>
    </div>
  );
}
