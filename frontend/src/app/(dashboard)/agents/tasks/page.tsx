"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  useTasks,
  useCreateTask,
  useApproveTask,
  useRejectTask,
  useCancelTask,
  useAgents,
} from "@/modules/agents/hooks";
import { TaskList } from "@/modules/agents/components/TaskList";
import { TaskDetail } from "@/modules/agents/components/TaskDetail";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { AgentTask, TaskStatus } from "@/modules/agents/types";
import { useTranslations } from "@/hooks/use-translations";

export default function TasksPage() {
  const t = useTranslations("agents");
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("");
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskAgentId, setNewTaskAgentId] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");

  // Dialog state
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const STATUS_OPTIONS: { value: TaskStatus | ""; label: string }[] = [
    { value: "", label: t("tasks.allStatuses") },
    { value: "pending", label: t("tasks.pending") },
    { value: "running", label: t("tasks.running") },
    { value: "awaiting_approval", label: t("tasks.awaitingApproval") },
    { value: "approved", label: t("tasks.approved") },
    { value: "rejected", label: t("tasks.rejected") },
    { value: "completed", label: t("tasks.completed") },
    { value: "failed", label: t("tasks.failed") },
    { value: "cancelled", label: t("tasks.cancelled") },
  ];

  const { data: agentsData } = useAgents();
  const { data: tasksData, isLoading } = useTasks(
    statusFilter ? { status: statusFilter as TaskStatus } : undefined
  );
  const createTask = useCreateTask();
  const approveTask = useApproveTask();
  const rejectTask = useRejectTask();
  const cancelTask = useCancelTask();

  const tasks = tasksData?.items || [];
  const agents = agentsData?.items || [];

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !newTaskAgentId) return;
    createTask.mutate(
      {
        agent_id: newTaskAgentId,
        title: newTaskTitle,
        description: newTaskDescription || undefined,
      },
      {
        onSuccess: () => {
          setShowCreateForm(false);
          setNewTaskTitle("");
          setNewTaskDescription("");
          setNewTaskAgentId("");
        },
      }
    );
  };

  const openApproveDialog = (taskId: string) => {
    setSelectedTaskId(taskId);
    setShowApproveDialog(true);
  };

  const openRejectDialog = (taskId: string) => {
    setSelectedTaskId(taskId);
    setRejectionReason("");
    setShowRejectDialog(true);
  };

  const handleApproveConfirm = () => {
    if (!selectedTaskId) return;
    setIsProcessing(true);
    approveTask.mutate(
      { taskId: selectedTaskId },
      {
        onSuccess: (updatedTask) => {
          setIsProcessing(false);
          setShowApproveDialog(false);
          setSelectedTaskId(null);
          // If we're in detail view, update the selected task
          if (selectedTask && selectedTask.id === selectedTaskId) {
            setSelectedTask(updatedTask);
          }
        },
        onError: () => {
          setIsProcessing(false);
        },
      }
    );
  };

  const handleRejectConfirm = () => {
    if (!selectedTaskId || !rejectionReason.trim()) return;
    setIsProcessing(true);
    rejectTask.mutate(
      { taskId: selectedTaskId, reason: rejectionReason.trim() },
      {
        onSuccess: (updatedTask) => {
          setIsProcessing(false);
          setShowRejectDialog(false);
          setSelectedTaskId(null);
          setRejectionReason("");
          // If we're in detail view, update the selected task
          if (selectedTask && selectedTask.id === selectedTaskId) {
            setSelectedTask(updatedTask);
          }
        },
        onError: () => {
          setIsProcessing(false);
        },
      }
    );
  };

  if (selectedTask) {
    return (
      <div className="space-y-4">
        <TaskDetail
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onApprove={() => openApproveDialog(selectedTask.id)}
          onReject={() => openRejectDialog(selectedTask.id)}
          onCancel={() => {
            cancelTask.mutate(
              { taskId: selectedTask.id, reason: "Cancelled by user" },
              {
                onSuccess: (updatedTask) => {
                  setSelectedTask(updatedTask);
                },
              }
            );
          }}
        />

        {/* Approve dialog */}
        <ConfirmDialog
          open={showApproveDialog}
          onOpenChange={(open) => {
            setShowApproveDialog(open);
            if (!open) setSelectedTaskId(null);
          }}
          onConfirm={handleApproveConfirm}
          title={t("tasks.approveTask")}
          description={t("tasks.approveDescription")}
          confirmText={t("tasks.approve")}
          cancelText={t("cancel")}
          variant="default"
          loading={isProcessing}
        />

        {/* Reject dialog */}
        <Dialog
          open={showRejectDialog}
          onOpenChange={(open) => {
            if (!isProcessing) {
              setShowRejectDialog(open);
              if (!open) {
                setSelectedTaskId(null);
                setRejectionReason("");
              }
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("tasks.rejectTask")}</DialogTitle>
              <DialogDescription>
                {t("tasks.rejectDescription")}
              </DialogDescription>
            </DialogHeader>
            <div className="py-2">
              <Textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder={t("tasks.rejectionReasonPlaceholder")}
                rows={3}
                aria-label={t("tasks.rejectionReason")}
                disabled={isProcessing}
              />
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowRejectDialog(false);
                  setSelectedTaskId(null);
                  setRejectionReason("");
                }}
                disabled={isProcessing}
                aria-label={t("tasks.cancelRejection")}
              >
                {t("cancel")}
              </Button>
              <Button
                variant="destructive"
                onClick={handleRejectConfirm}
                disabled={isProcessing || !rejectionReason.trim()}
                aria-label={t("tasks.confirmRejection")}
              >
                {isProcessing && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {isProcessing ? t("tasks.processing") : t("tasks.reject")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("tasks.title")}</h1>
          <p className="text-muted-foreground">
            {t("tasks.subtitle")}
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          aria-label={showCreateForm ? t("tasks.cancelCreate") : t("tasks.createNewTask")}
        >
          {showCreateForm ? t("cancel") : t("tasks.newTask")}
        </button>
      </div>

      {/* Create task form */}
      {showCreateForm && (
        <form
          onSubmit={handleCreateTask}
          className="rounded-lg border p-4 space-y-3"
        >
          <h3 className="text-sm font-semibold">{t("tasks.createTask")}</h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className="block text-xs font-medium mb-1">{t("tasks.agent")}</label>
              <select
                value={newTaskAgentId}
                onChange={(e) => setNewTaskAgentId(e.target.value)}
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                required
              >
                <option value="">{t("tasks.selectAgent")}</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">{t("tasks.taskTitle")}</label>
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder={t("tasks.taskTitlePlaceholder")}
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">
              {t("tasks.taskDescription")}
            </label>
            <textarea
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              placeholder={t("tasks.taskDescriptionPlaceholder")}
              className="w-full rounded-md border px-2 py-1.5 text-sm"
              rows={2}
            />
          </div>
          <button
            type="submit"
            disabled={createTask.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            aria-label={t("tasks.submitTask")}
          >
            {createTask.isPending ? t("tasks.creating") : t("tasks.createTask")}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}
          className="rounded-md border px-3 py-1.5 text-sm"
          aria-label={t("tasks.filterByStatus")}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="text-sm text-muted-foreground">
          {t("tasks.totalTasks", { count: tasksData?.total_count ?? 0 })}
        </span>
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="text-muted-foreground">{t("tasks.loadingTasks")}</div>
      ) : (
        <TaskList
          tasks={tasks}
          onSelect={setSelectedTask}
          onApprove={(task) => openApproveDialog(task.id)}
          onReject={(task) => openRejectDialog(task.id)}
          onCancel={(task) =>
            cancelTask.mutate({ taskId: task.id, reason: "Cancelled by user" })
          }
        />
      )}

      {/* Approve dialog */}
      <ConfirmDialog
        open={showApproveDialog}
        onOpenChange={(open) => {
          setShowApproveDialog(open);
          if (!open) setSelectedTaskId(null);
        }}
        onConfirm={handleApproveConfirm}
        title={t("tasks.approveTask")}
        description={t("tasks.approveDescription")}
        confirmText={t("tasks.approve")}
        cancelText={t("cancel")}
        variant="default"
        loading={isProcessing}
      />

      {/* Reject dialog */}
      <Dialog
        open={showRejectDialog}
        onOpenChange={(open) => {
          if (!isProcessing) {
            setShowRejectDialog(open);
            if (!open) {
              setSelectedTaskId(null);
              setRejectionReason("");
            }
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("tasks.rejectTask")}</DialogTitle>
            <DialogDescription>
              {t("tasks.rejectDescription")}
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder={t("tasks.rejectionReasonPlaceholder")}
              rows={3}
              aria-label={t("tasks.rejectionReason")}
              disabled={isProcessing}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowRejectDialog(false);
                setSelectedTaskId(null);
                setRejectionReason("");
              }}
              disabled={isProcessing}
              aria-label={t("tasks.cancelRejection")}
            >
              {t("cancel")}
            </Button>
            <Button
              variant="destructive"
              onClick={handleRejectConfirm}
              disabled={isProcessing || !rejectionReason.trim()}
              aria-label={t("tasks.confirmRejection")}
            >
              {isProcessing && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {isProcessing ? t("tasks.processing") : t("tasks.reject")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
