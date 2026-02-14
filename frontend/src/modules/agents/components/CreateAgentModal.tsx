"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { X } from "lucide-react";
import { useCreateCustomAgent } from "../hooks";

interface CreateAgentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface TaskType {
  id: string;
  key: string;
  label: string;
  description: string;
}

const EMOJI_OPTIONS = ["🤖", "📖", "🔍", "✍️", "✂️", "📢", "🎯", "💡", "📊", "🧪"];

export function CreateAgentModal({ open, onOpenChange }: CreateAgentModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "custom",
    icon: "🤖",
    systemPrompt: "",
    model: "claude-sonnet-4-5-20250929",
    maxTokens: 4096,
    temperature: 0.7,
    defaultMode: "suggest",
  });

  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);
  const [newTaskType, setNewTaskType] = useState({
    key: "",
    label: "",
    description: "",
  });

  const { mutate: createAgent, isPending } = useCreateCustomAgent();

  const handleAddTaskType = () => {
    if (!newTaskType.key || !newTaskType.label || !newTaskType.description) {
      return;
    }

    if (taskTypes.length >= 5) {
      return;
    }

    setTaskTypes([
      ...taskTypes,
      {
        id: `task-${Date.now()}`,
        ...newTaskType,
      },
    ]);

    setNewTaskType({
      key: "",
      label: "",
      description: "",
    });
  };

  const handleRemoveTaskType = (id: string) => {
    setTaskTypes(taskTypes.filter((t) => t.id !== id));
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.systemPrompt) {
      return;
    }

    createAgent(
      {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        icon: formData.icon,
        system_prompt: formData.systemPrompt,
        model: formData.model,
        max_tokens: formData.maxTokens,
        temperature: formData.temperature,
        default_execution_mode: formData.defaultMode,
        task_types: taskTypes.map(({ id, ...rest }) => rest),
      },
      {
        onSuccess: () => {
          onOpenChange(false);
          // Reset form
          setFormData({
            name: "",
            description: "",
            category: "custom",
            icon: "🤖",
            systemPrompt: "",
            model: "claude-sonnet-4-5-20250929",
            maxTokens: 4096,
            temperature: 0.7,
            defaultMode: "suggest",
          });
          setTaskTypes([]);
          setNewTaskType({
            key: "",
            label: "",
            description: "",
          });
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Custom Agent</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <Label htmlFor="agent-name">
              Agent Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="agent-name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Character Development Specialist"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agent-description">Description</Label>
            <Textarea
              id="agent-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what this agent does..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => setFormData({ ...formData, category: value })}
              >
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom</SelectItem>
                  <SelectItem value="research">Research</SelectItem>
                  <SelectItem value="writing">Writing</SelectItem>
                  <SelectItem value="editing">Editing</SelectItem>
                  <SelectItem value="marketing">Marketing</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="icon">Icon</Label>
              <Select value={formData.icon} onValueChange={(value) => setFormData({ ...formData, icon: value })}>
                <SelectTrigger id="icon">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EMOJI_OPTIONS.map((emoji) => (
                    <SelectItem key={emoji} value={emoji}>
                      {emoji} {emoji}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="system-prompt">
              System Prompt <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="system-prompt"
              value={formData.systemPrompt}
              onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
              placeholder="Enter the system prompt that defines this agent's behavior and capabilities..."
              rows={8}
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Task Types</Label>
              <span className="text-sm text-muted-foreground">{taskTypes.length}/5</span>
            </div>

            {taskTypes.length > 0 && (
              <div className="space-y-2">
                {taskTypes.map((taskType) => (
                  <div key={taskType.id} className="flex items-start gap-2 p-3 border rounded-lg">
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium">{taskType.key}</span>
                        <span className="text-sm">-</span>
                        <span className="font-medium">{taskType.label}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{taskType.description}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveTaskType(taskType.id)}
                      className="h-8 w-8"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {taskTypes.length < 5 && (
              <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="task-key" className="text-sm">
                      Key
                    </Label>
                    <Input
                      id="task-key"
                      value={newTaskType.key}
                      onChange={(e) => setNewTaskType({ ...newTaskType, key: e.target.value })}
                      placeholder="e.g., character_profile"
                      className="font-mono text-sm"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="task-label" className="text-sm">
                      Label
                    </Label>
                    <Input
                      id="task-label"
                      value={newTaskType.label}
                      onChange={(e) => setNewTaskType({ ...newTaskType, label: e.target.value })}
                      placeholder="e.g., Character Profile"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="task-description" className="text-sm">
                    Description
                  </Label>
                  <Input
                    id="task-description"
                    value={newTaskType.description}
                    onChange={(e) => setNewTaskType({ ...newTaskType, description: e.target.value })}
                    placeholder="e.g., Create detailed character profiles"
                  />
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddTaskType}
                  disabled={!newTaskType.key || !newTaskType.label || !newTaskType.description}
                  className="w-full"
                >
                  + Add Type
                </Button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Select value={formData.model} onValueChange={(value) => setFormData({ ...formData, model: value })}>
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
                value={formData.maxTokens.toString()}
                onValueChange={(value) => setFormData({ ...formData, maxTokens: parseInt(value) })}
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
          </div>

          <div className="space-y-2">
            <Label htmlFor="temperature">Temperature: {formData.temperature.toFixed(1)}</Label>
            <Slider
              id="temperature"
              min={0}
              max={1}
              step={0.1}
              value={[formData.temperature]}
              onValueChange={(values) => setFormData({ ...formData, temperature: values[0] })}
            />
          </div>

          <div className="space-y-2">
            <Label>Default Mode</Label>
            <RadioGroup
              value={formData.defaultMode}
              onValueChange={(value) => setFormData({ ...formData, defaultMode: value })}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="draft" id="default-mode-draft" />
                <Label htmlFor="default-mode-draft" className="font-normal cursor-pointer">
                  Draft Only
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggest" id="default-mode-suggest" />
                <Label htmlFor="default-mode-suggest" className="font-normal cursor-pointer">
                  Suggest
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="auto" id="default-mode-auto" />
                <Label htmlFor="default-mode-auto" className="font-normal cursor-pointer">
                  Auto-Apply
                </Label>
              </div>
            </RadioGroup>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !formData.name || !formData.systemPrompt}>
            {isPending ? "Creating..." : "Create Agent"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
