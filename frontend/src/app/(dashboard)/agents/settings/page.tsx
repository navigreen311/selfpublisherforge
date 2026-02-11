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
import { useTranslations } from "@/hooks/use-translations";

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
  const t = useTranslations("agents");
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
          <label className="block text-sm font-medium mb-1">{t("settings.name")}</label>
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
            {t("settings.permissionLevel")}
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
          <label className="block text-sm font-medium mb-1">{t("settings.modelId")}</label>
          <input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t("settings.maxTokens")}</label>
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
            {t("settings.temperature", { value: temperature.toFixed(1) })}
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
            {t("settings.enabled")}
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("settings.description")}</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full rounded-md border px-3 py-2 text-sm"
          rows={2}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("settings.systemPrompt")}</label>
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
        {isSaving ? t("settings.saving") : t("settings.saveConfiguration")}
      </button>
    </form>
  );
}

export default function AgentSettingsPage() {
  const t = useTranslations("agents");
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
        <h1 className="text-2xl font-bold">{t("settings.title")}</h1>
        <p className="text-muted-foreground">
          {t("settings.subtitle")}
        </p>
      </div>

      {/* Agent selector */}
      <div>
        <label className="block text-sm font-medium mb-1">{t("settings.selectAgent")}</label>
        <select
          value={selectedAgentId}
          onChange={(e) => setSelectedAgentId(e.target.value)}
          className="rounded-md border px-3 py-2 text-sm w-full max-w-sm"
        >
          <option value="">{t("settings.chooseAgent")}</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.agent_type})
            </option>
          ))}
        </select>
      </div>

      {agentsLoading && (
        <div className="text-muted-foreground">{t("settings.loadingAgents")}</div>
      )}

      {/* Agent config */}
      {selectedAgent && (
        <section className="space-y-6">
          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">
              {t("settings.configuration", { name: selectedAgent.name })}
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
                {t("settings.configSaved")}
              </div>
            )}
          </div>

          {/* Budget */}
          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">{t("settings.budget")}</h2>
            {selectedBudget ? (
              <div className="space-y-4">
                <BudgetMeter
                  budget={selectedBudget}
                  agentName={selectedAgent.name}
                />
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      {t("settings.dailyTokenLimit")}
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
                      {t("settings.dailyUsdLimit")}
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
                      {t("settings.monthlyUsdLimit")}
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
                {t("settings.noBudget")}
              </p>
            )}
          </div>
        </section>
      )}

      {/* Audit trail */}
      <section>
        <h2 className="text-lg font-semibold mb-4">{t("settings.auditTrail")}</h2>
        <AuditLog
          entries={auditEntries}
          hasMore={auditData?.has_more}
        />
      </section>
    </div>
  );
}
