"use client";

import * as React from "react";
import { X, Plus, Trash2, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DictationCommand } from "../types";

interface VoiceCommandPanelProps {
  commands: DictationCommand[];
  onToggle: (id: string, active: boolean) => void;
  onAdd: (phrase: string, action: string) => void;
  onDelete: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

const CUSTOM_ACTIONS = [
  { value: "insert_text", label: "Insert text" },
  { value: "new_paragraph", label: "New paragraph" },
  { value: "new_line", label: "New line" },
  { value: "delete_word", label: "Delete word" },
  { value: "undo", label: "Undo" },
  { value: "bold", label: "Bold" },
  { value: "italic", label: "Italic" },
  { value: "chapter_break", label: "Chapter break" },
  { value: "stop_dictation", label: "Stop dictation" },
];

function CommandRow({
  command,
  onToggle,
  onDelete,
}: {
  command: DictationCommand;
  onToggle: (id: string, active: boolean) => void;
  onDelete?: (id: string) => void;
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-md px-3 py-2 transition-colors hover:bg-muted/50"
      role="listitem"
    >
      <Switch
        checked={command.active}
        onCheckedChange={(checked) => onToggle(command.id, checked)}
        aria-label={`Toggle command: ${command.phrase}`}
      />
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">{command.phrase}</p>
        <p className="truncate text-xs text-muted-foreground">
          {command.action}
        </p>
      </div>
      {!command.builtIn && onDelete && (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
          onClick={() => onDelete(command.id)}
          aria-label={`Delete command: ${command.phrase}`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}

export function VoiceCommandPanel({
  commands,
  onToggle,
  onAdd,
  onDelete,
  isOpen,
  onClose,
}: VoiceCommandPanelProps) {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [showAddForm, setShowAddForm] = React.useState(false);
  const [newPhrase, setNewPhrase] = React.useState("");
  const [newAction, setNewAction] = React.useState("");
  const panelRef = React.useRef<HTMLDivElement>(null);

  const builtInCommands = React.useMemo(
    () => commands.filter((c) => c.builtIn),
    [commands]
  );
  const customCommands = React.useMemo(
    () => commands.filter((c) => !c.builtIn),
    [commands]
  );

  const filteredBuiltIn = React.useMemo(() => {
    if (!searchQuery) return builtInCommands;
    const q = searchQuery.toLowerCase();
    return builtInCommands.filter(
      (c) =>
        c.phrase.toLowerCase().includes(q) ||
        c.action.toLowerCase().includes(q)
    );
  }, [builtInCommands, searchQuery]);

  const filteredCustom = React.useMemo(() => {
    if (!searchQuery) return customCommands;
    const q = searchQuery.toLowerCase();
    return customCommands.filter(
      (c) =>
        c.phrase.toLowerCase().includes(q) ||
        c.action.toLowerCase().includes(q)
    );
  }, [customCommands, searchQuery]);

  const handleAdd = React.useCallback(() => {
    if (newPhrase.trim() && newAction) {
      onAdd(newPhrase.trim(), newAction);
      setNewPhrase("");
      setNewAction("");
      setShowAddForm(false);
    }
  }, [newPhrase, newAction, onAdd]);

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleAdd();
      }
    },
    [handleAdd]
  );

  // Trap focus and handle Escape
  React.useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={cn(
          "fixed right-0 top-0 z-50 flex h-full w-96 flex-col border-l bg-background shadow-xl",
          "animate-in slide-in-from-right duration-300"
        )}
        role="dialog"
        aria-label="Voice commands"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-base font-semibold">Voice Commands</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Search */}
        <div className="border-b px-4 py-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search commands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 pl-9 text-sm"
              aria-label="Filter voice commands"
            />
          </div>
        </div>

        {/* Command lists */}
        <div className="flex-1 overflow-y-auto">
          {/* Built-in commands */}
          <div className="px-4 py-3">
            <div className="mb-2 flex items-center gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Built-in Commands
              </h3>
              <Badge variant="secondary" className="text-xs">
                {filteredBuiltIn.length}
              </Badge>
            </div>
            <div className="space-y-0.5" role="list">
              {filteredBuiltIn.map((command) => (
                <CommandRow
                  key={command.id}
                  command={command}
                  onToggle={onToggle}
                />
              ))}
              {filteredBuiltIn.length === 0 && (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  No matching built-in commands
                </p>
              )}
            </div>
          </div>

          {/* Custom commands */}
          <div className="border-t px-4 py-3">
            <div className="mb-2 flex items-center gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Custom Commands
              </h3>
              <Badge variant="secondary" className="text-xs">
                {filteredCustom.length}
              </Badge>
            </div>
            <div className="space-y-0.5" role="list">
              {filteredCustom.map((command) => (
                <CommandRow
                  key={command.id}
                  command={command}
                  onToggle={onToggle}
                  onDelete={onDelete}
                />
              ))}
              {filteredCustom.length === 0 && !showAddForm && (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  {searchQuery
                    ? "No matching custom commands"
                    : "No custom commands yet"}
                </p>
              )}
            </div>

            {/* Add custom command form */}
            {showAddForm ? (
              <div className="mt-3 space-y-2 rounded-md border bg-muted/30 p-3">
                <div className="space-y-1.5">
                  <Label htmlFor="new-phrase" className="text-xs">
                    Trigger phrase
                  </Label>
                  <Input
                    id="new-phrase"
                    placeholder='e.g., "scene break"'
                    value={newPhrase}
                    onChange={(e) => setNewPhrase(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="h-8 text-sm"
                    autoFocus
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="new-action" className="text-xs">
                    Action
                  </Label>
                  <Select value={newAction} onValueChange={setNewAction}>
                    <SelectTrigger id="new-action" className="h-8 text-xs">
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      {CUSTOM_ACTIONS.map((action) => (
                        <SelectItem
                          key={action.value}
                          value={action.value}
                          className="text-xs"
                        >
                          {action.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => {
                      setShowAddForm(false);
                      setNewPhrase("");
                      setNewAction("");
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    className="h-7 text-xs"
                    onClick={handleAdd}
                    disabled={!newPhrase.trim() || !newAction}
                  >
                    Add
                  </Button>
                </div>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full"
                onClick={() => setShowAddForm(true)}
              >
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Add Custom Command
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
