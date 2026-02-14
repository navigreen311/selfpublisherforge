"use client";

import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useConfigureAgent } from "../hooks";

interface ConfigureAgentPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent: any;
}

export function ConfigureAgentPanel({ open, onOpenChange, agent }: ConfigureAgentPanelProps) {
  const [activeTab, setActiveTab] = useState("general");
  const [config, setConfig] = useState({
    name: agent?.name || "",
    description: agent?.description || "",
    defaultMode: agent?.defaultMode || "suggest",
    model: agent?.model || "claude-sonnet-4-5-20250929",
    maxTokens: agent?.maxTokens || 4096,
    temperature: agent?.temperature || 0.7,
    maxCostPerTask: agent?.maxCostPerTask || 5.0,
    monthlyBudgetCap: agent?.monthlyBudgetCap || 100.0,
    systemPrompt: agent?.systemPrompt || "",
    contextSources: {
      bookMetadata: agent?.contextSources?.bookMetadata ?? true,
      knowledgeVault: agent?.contextSources?.knowledgeVault ?? true,
      marketResearch: agent?.contextSources?.marketResearch ?? false,
      writingStudio: agent?.contextSources?.writingStudio ?? false,
      analytics: agent?.contextSources?.analytics ?? false,
    },
    responseFormat: agent?.responseFormat || "markdown",
    maxRetries: agent?.maxRetries || 3,
    timeoutSeconds: agent?.timeoutSeconds || 120,
  });

  const { mutate: configureAgent, isPending } = useConfigureAgent();

  const handleSave = () => {
    configureAgent(
      {
        agentId: agent.id,
        data: config,
      },
      {
        onSuccess: () => {
          onOpenChange(false);
        },
      }
    );
  };

  const handleReset = () => {
    setConfig({
      name: agent?.name || "",
      description: agent?.description || "",
      defaultMode: "suggest",
      model: "claude-sonnet-4-5-20250929",
      maxTokens: 4096,
      temperature: 0.7,
      maxCostPerTask: 5.0,
      monthlyBudgetCap: 100.0,
      systemPrompt: agent?.systemPrompt || "",
      contextSources: {
        bookMetadata: true,
        knowledgeVault: true,
        marketResearch: false,
        writingStudio: false,
        analytics: false,
      },
      responseFormat: "markdown",
      maxRetries: 3,
      timeoutSeconds: 120,
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Configure Agent: {agent?.name}</SheetTitle>
        </SheetHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="prompts">Prompts</TabsTrigger>
            <TabsTrigger value="permissions">Permissions</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general" className="space-y-6 mt-6">
            <div className="space-y-2">
              <Label htmlFor="agent-name">Agent Name</Label>
              <Input
                id="agent-name"
                value={config.name}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="Enter agent name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="agent-description">Description</Label>
              <Textarea
                id="agent-description"
                value={config.description}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="Enter agent description"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Default Execution Mode</Label>
              <RadioGroup
                value={config.defaultMode}
                onValueChange={(value) => setConfig({ ...config, defaultMode: value })}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="draft" id="mode-draft" />
                  <Label htmlFor="mode-draft" className="font-normal cursor-pointer">
                    Draft Only
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="suggest" id="mode-suggest" />
                  <Label htmlFor="mode-suggest" className="font-normal cursor-pointer">
                    Suggest
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="auto" id="mode-auto" />
                  <Label htmlFor="mode-auto" className="font-normal cursor-pointer">
                    Auto-Apply
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Select value={config.model} onValueChange={(value) => setConfig({ ...config, model: value })}>
                <SelectTrigger id="model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</SelectItem>
                  <SelectItem value="claude-opus-4-20250514">Claude Opus 4</SelectItem>
                  <SelectItem value="claude-haiku-4-5-20251001">Claude Haiku 4.5</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-tokens">Max Tokens</Label>
              <Select
                value={config.maxTokens.toString()}
                onValueChange={(value) => setConfig({ ...config, maxTokens: parseInt(value) })}
              >
                <SelectTrigger id="max-tokens">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1024">1024</SelectItem>
                  <SelectItem value="2048">2048</SelectItem>
                  <SelectItem value="4096">4096</SelectItem>
                  <SelectItem value="8192">8192</SelectItem>
                  <SelectItem value="16384">16384</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="temperature">
                Temperature: {config.temperature.toFixed(1)}
              </Label>
              <Slider
                id="temperature"
                min={0}
                max={1}
                step={0.1}
                value={[config.temperature]}
                onValueChange={(values) => setConfig({ ...config, temperature: values[0] })}
              />
            </div>

            <div className="space-y-4 pt-4 border-t">
              <h4 className="font-medium">Budget Limits</h4>

              <div className="space-y-2">
                <Label htmlFor="max-cost">Max cost per task ($)</Label>
                <Input
                  id="max-cost"
                  type="number"
                  step="0.01"
                  value={config.maxCostPerTask}
                  onChange={(e) => setConfig({ ...config, maxCostPerTask: parseFloat(e.target.value) })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="monthly-cap">Monthly budget cap ($)</Label>
                <Input
                  id="monthly-cap"
                  type="number"
                  step="0.01"
                  value={config.monthlyBudgetCap}
                  onChange={(e) => setConfig({ ...config, monthlyBudgetCap: parseFloat(e.target.value) })}
                />
              </div>

              <p className="text-sm text-muted-foreground">
                Agent pauses when budget hit, requires manual resume
              </p>
            </div>
          </TabsContent>

          {/* Prompts Tab */}
          <TabsContent value="prompts" className="space-y-6 mt-6">
            <div className="space-y-2">
              <Label htmlFor="system-prompt">System Prompt</Label>
              <Textarea
                id="system-prompt"
                value={config.systemPrompt}
                onChange={(e) => setConfig({ ...config, systemPrompt: e.target.value })}
                placeholder="Enter system prompt for the agent"
                rows={12}
                className="font-mono text-sm"
              />
            </div>

            <div className="space-y-4">
              <Label>Context Sources</Label>
              <p className="text-sm text-muted-foreground">
                Select what data the agent can access
              </p>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="context-book"
                    checked={config.contextSources.bookMetadata}
                    onCheckedChange={(checked) =>
                      setConfig({
                        ...config,
                        contextSources: { ...config.contextSources, bookMetadata: checked as boolean },
                      })
                    }
                  />
                  <Label htmlFor="context-book" className="font-normal cursor-pointer">
                    Book metadata from linked project
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="context-vault"
                    checked={config.contextSources.knowledgeVault}
                    onCheckedChange={(checked) =>
                      setConfig({
                        ...config,
                        contextSources: { ...config.contextSources, knowledgeVault: checked as boolean },
                      })
                    }
                  />
                  <Label htmlFor="context-vault" className="font-normal cursor-pointer">
                    Knowledge Vault entries
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="context-research"
                    checked={config.contextSources.marketResearch}
                    onCheckedChange={(checked) =>
                      setConfig({
                        ...config,
                        contextSources: { ...config.contextSources, marketResearch: checked as boolean },
                      })
                    }
                  />
                  <Label htmlFor="context-research" className="font-normal cursor-pointer">
                    Market Research data
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="context-studio"
                    checked={config.contextSources.writingStudio}
                    onCheckedChange={(checked) =>
                      setConfig({
                        ...config,
                        contextSources: { ...config.contextSources, writingStudio: checked as boolean },
                      })
                    }
                  />
                  <Label htmlFor="context-studio" className="font-normal cursor-pointer">
                    Writing Studio content
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="context-analytics"
                    checked={config.contextSources.analytics}
                    onCheckedChange={(checked) =>
                      setConfig({
                        ...config,
                        contextSources: { ...config.contextSources, analytics: checked as boolean },
                      })
                    }
                  />
                  <Label htmlFor="context-analytics" className="font-normal cursor-pointer">
                    Analytics data
                  </Label>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Permissions Tab */}
          <TabsContent value="permissions" className="space-y-6 mt-6">
            <div className="space-y-4">
              <h4 className="font-medium">Default execution mode per task type</h4>
              <p className="text-sm text-muted-foreground">
                Configure how the agent handles different types of tasks by default
              </p>

              <div className="space-y-4 pt-4">
                {agent?.taskTypes?.map((taskType: any) => (
                  <div key={taskType.key} className="space-y-2 p-4 border rounded-lg">
                    <Label className="font-medium">{taskType.label}</Label>
                    <p className="text-sm text-muted-foreground">{taskType.description}</p>
                    <RadioGroup defaultValue="suggest" className="pt-2">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="draft" id={`${taskType.key}-draft`} />
                        <Label htmlFor={`${taskType.key}-draft`} className="font-normal cursor-pointer">
                          Draft Only
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="suggest" id={`${taskType.key}-suggest`} />
                        <Label htmlFor={`${taskType.key}-suggest`} className="font-normal cursor-pointer">
                          Suggest
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="auto" id={`${taskType.key}-auto`} />
                        <Label htmlFor={`${taskType.key}-auto`} className="font-normal cursor-pointer">
                          Auto-Apply
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>
                )) || (
                  <p className="text-sm text-muted-foreground">No task types configured for this agent</p>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Advanced Tab */}
          <TabsContent value="advanced" className="space-y-6 mt-6">
            <div className="space-y-2">
              <Label htmlFor="response-format">Response Format</Label>
              <Select
                value={config.responseFormat}
                onValueChange={(value) => setConfig({ ...config, responseFormat: value })}
              >
                <SelectTrigger id="response-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="plain">Plain Text</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-retries">Max Retries</Label>
              <Input
                id="max-retries"
                type="number"
                min="0"
                max="10"
                value={config.maxRetries}
                onChange={(e) => setConfig({ ...config, maxRetries: parseInt(e.target.value) })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                min="30"
                max="600"
                step="10"
                value={config.timeoutSeconds}
                onChange={(e) => setConfig({ ...config, timeoutSeconds: parseInt(e.target.value) })}
              />
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 mt-6 pt-6 border-t">
          <Button variant="outline" onClick={handleReset} disabled={isPending}>
            Reset to Defaults
          </Button>
          <Button onClick={handleSave} disabled={isPending}>
            {isPending ? "Saving..." : "Save Configuration"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
