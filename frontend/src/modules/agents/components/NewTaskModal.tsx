"use client";

import { useState, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Card, CardContent } from "@/components/ui/card";
import { AGENT_TASK_TYPES, TaskCreatePayload } from "../types";
import { useCreateTask } from "../hooks";

interface NewTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId?: string;
  agents: any[];
}

const EXECUTION_MODES = [
  {
    value: "draft_only",
    label: "Draft Only",
    description: "Generate a draft for review without applying changes"
  },
  {
    value: "suggest",
    label: "Suggest",
    description: "Generate suggestions and wait for approval before applying"
  },
  {
    value: "auto_apply",
    label: "Auto-Apply",
    description: "Automatically apply changes after generation"
  }
];

const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Normal" },
  { value: "high", label: "High" },
  { value: "critical", label: "Urgent" }
];

const MAX_TOKENS_OPTIONS = [
  { value: 1024, label: "1024" },
  { value: 2048, label: "2048" },
  { value: 4096, label: "4096" },
  { value: 8192, label: "8192" }
];

const TOKEN_COST_RATE = 0.00003; // Rough estimate: $0.00003 per token

export function NewTaskModal({ open, onOpenChange, agentId, agents }: NewTaskModalProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agentId || "");
  const [taskType, setTaskType] = useState<string>("");
  const [bookId, setBookId] = useState<string>("");
  const [instructions, setInstructions] = useState<string>("");
  const [executionMode, setExecutionMode] = useState<string>("suggest");
  const [priority, setPriority] = useState<string>("medium");
  const [maxTokens, setMaxTokens] = useState<number>(4096);

  const createTaskMutation = useCreateTask();

  // Get the selected agent and its task types
  const selectedAgent = useMemo(() => {
    return agents.find(agent => agent.id === selectedAgentId);
  }, [agents, selectedAgentId]);

  const availableTaskTypes = useMemo(() => {
    if (!selectedAgent) return [];
    return AGENT_TASK_TYPES[selectedAgent.agent_type] || [];
  }, [selectedAgent]);

  // Calculate estimated cost
  const estimatedCost = useMemo(() => {
    return (maxTokens * TOKEN_COST_RATE).toFixed(2);
  }, [maxTokens]);

  // Reset task type when agent changes
  const handleAgentChange = (newAgentId: string) => {
    setSelectedAgentId(newAgentId);
    setTaskType(""); // Reset task type when agent changes
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!selectedAgentId) {
      alert("Please select an agent");
      return;
    }
    if (!taskType) {
      alert("Please select a task type");
      return;
    }
    if (!instructions.trim()) {
      alert("Please provide instructions");
      return;
    }
    if (instructions.length > 4000) {
      alert("Instructions must be 4000 characters or less");
      return;
    }

    try {
      // Find the selected task type to get its label for the title
      const selectedTaskTypeObj = availableTaskTypes.find(t => t.key === taskType);
      const taskTitle = selectedTaskTypeObj ? selectedTaskTypeObj.label : "New Task";

      await createTaskMutation.mutateAsync({
        agent_id: selectedAgentId,
        title: taskTitle,
        description: instructions,
        priority: priority as any,
        input_data: {
          task_type: taskType,
          book_id: bookId || undefined,
          instructions,
          execution_mode: executionMode,
          max_tokens: maxTokens
        }
      });

      // Reset form and close modal on success
      setTaskType("");
      setBookId("");
      setInstructions("");
      setExecutionMode("suggest");
      setPriority("medium");
      setMaxTokens(4096);
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to create task:", error);
      alert("Failed to create task. Please try again.");
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  const isFormValid = selectedAgentId && taskType && instructions.trim().length > 0 && instructions.length <= 4000;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Agent Selector */}
          <div className="space-y-2">
            <Label htmlFor="agent">Agent</Label>
            <Select value={selectedAgentId} onValueChange={handleAgentChange}>
              <SelectTrigger id="agent">
                <SelectValue placeholder="Select an agent" />
              </SelectTrigger>
              <SelectContent>
                {agents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Task Type */}
          {selectedAgentId && availableTaskTypes.length > 0 && (
            <div className="space-y-2">
              <Label>Task Type</Label>
              <RadioGroup value={taskType} onValueChange={setTaskType}>
                <div className="grid grid-cols-2 gap-3">
                  {availableTaskTypes.map((type) => (
                    <Card
                      key={type.key}
                      className={`cursor-pointer transition-colors ${
                        taskType === type.key ? "border-primary bg-primary/5" : "hover:border-primary/50"
                      }`}
                      onClick={() => setTaskType(type.key)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value={type.key} id={type.key} />
                          <Label htmlFor={type.key} className="flex items-center gap-2 cursor-pointer">
                            <span className="text-lg">{type.icon}</span>
                            <span className="text-sm font-medium">{type.label}</span>
                          </Label>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </RadioGroup>
            </div>
          )}

          {/* Context Book */}
          <div className="space-y-2">
            <Label htmlFor="book">Context Book (Optional)</Label>
            <Select value={bookId} onValueChange={setBookId}>
              <SelectTrigger id="book">
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None</SelectItem>
                {/* TODO: Add book options when books module is available */}
              </SelectContent>
            </Select>
          </div>

          {/* Instructions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="instructions">Instructions *</Label>
              <span className="text-xs text-muted-foreground">
                {instructions.length} / 4000
              </span>
            </div>
            <Textarea
              id="instructions"
              placeholder="Provide detailed instructions for the task..."
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={6}
              maxLength={4000}
              required
            />
          </div>

          {/* Execution Mode */}
          <div className="space-y-2">
            <Label>Execution Mode</Label>
            <RadioGroup value={executionMode} onValueChange={setExecutionMode}>
              <div className="space-y-3">
                {EXECUTION_MODES.map((mode) => (
                  <div key={mode.value} className="flex items-start space-x-3">
                    <RadioGroupItem value={mode.value} id={mode.value} className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor={mode.value} className="cursor-pointer">
                        <div className="font-medium">{mode.label}</div>
                        <div className="text-sm text-muted-foreground">{mode.description}</div>
                      </Label>
                    </div>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </div>

          {/* Priority and Max Tokens Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Priority */}
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger id="priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITIES.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <Label htmlFor="maxTokens">Max Tokens</Label>
              <Select value={String(maxTokens)} onValueChange={(val) => setMaxTokens(Number(val))}>
                <SelectTrigger id="maxTokens">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MAX_TOKENS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Estimated Cost */}
          <div className="rounded-lg bg-muted p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Estimated Cost:</span>
              <span className="font-semibold">~${estimatedCost}</span>
            </div>
          </div>

          {/* Dialog Footer */}
          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createTaskMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isFormValid || createTaskMutation.isPending}
            >
              {createTaskMutation.isPending ? "Creating..." : "Run Task →"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
