"use client";

import { useState, useMemo } from "react";
import { format, isPast } from "date-fns";
import { cn } from "@/lib/utils";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  ArrowUpDown,
  Circle,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { usePipelineStages } from "../hooks";
import { TaskDetailPanel } from "./TaskDetailPanel";
import type { PipelineTask, PipelineStage, TaskStatus } from "../types";

const statusIcons: Record<TaskStatus, React.ReactNode> = {
  pending: <Circle className="h-3.5 w-3.5 text-gray-400" />,
  in_progress: <Loader2 className="h-3.5 w-3.5 text-blue-500" />,
  blocked: <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />,
  completed: <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />,
  cancelled: <XCircle className="h-3.5 w-3.5 text-red-400" />,
};

const statusColors: Record<TaskStatus, string> = {
  pending: "bg-gray-100 text-gray-700",
  in_progress: "bg-blue-100 text-blue-700",
  blocked: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-600",
};

type SortKey = "title" | "status" | "priority" | "due_date" | "stage";
type SortDir = "asc" | "desc";

interface ListViewProps {
  pipelineId: string;
  tasks: PipelineTask[];
}

export function ListView({ pipelineId, tasks }: ListViewProps) {
  const { data: stages } = usePipelineStages(pipelineId);
  const stageList = stages ?? [];

  const [selectedTask, setSelectedTask] = useState<PipelineTask | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("due_date");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterStatus, setFilterStatus] = useState<TaskStatus | "">("");
  const [filterPriority, setFilterPriority] = useState<string>("");

  const stageMap = useMemo(() => {
    const map: Record<string, PipelineStage> = {};
    for (const s of stageList) {
      map[s.id] = s;
    }
    return map;
  }, [stageList]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const filteredTasks = useMemo(() => {
    let result = [...tasks];

    if (filterStatus) {
      result = result.filter((t) => t.status === filterStatus);
    }
    if (filterPriority) {
      result = result.filter((t) => t.priority === filterPriority);
    }

    result.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      switch (sortKey) {
        case "title":
          return dir * a.title.localeCompare(b.title);
        case "status":
          return dir * a.status.localeCompare(b.status);
        case "priority": {
          const priorityOrder = { high: 0, medium: 1, low: 2 };
          const ap =
            priorityOrder[a.priority as keyof typeof priorityOrder] ?? 3;
          const bp =
            priorityOrder[b.priority as keyof typeof priorityOrder] ?? 3;
          return dir * (ap - bp);
        }
        case "due_date": {
          const ad = a.due_date ? new Date(a.due_date).getTime() : Infinity;
          const bd = b.due_date ? new Date(b.due_date).getTime() : Infinity;
          return dir * (ad - bd);
        }
        case "stage": {
          const an = a.stage_id ? stageMap[a.stage_id]?.name ?? "" : "";
          const bn = b.stage_id ? stageMap[b.stage_id]?.name ?? "" : "";
          return dir * an.localeCompare(bn);
        }
        default:
          return 0;
      }
    });

    return result;
  }, [tasks, filterStatus, filterPriority, sortKey, sortDir, stageMap]);

  function SortButton({ label, sortKeyValue }: { label: string; sortKeyValue: SortKey }) {
    return (
      <button
        onClick={() => toggleSort(sortKeyValue)}
        className="flex items-center gap-1 hover:text-foreground"
      >
        {label}
        <ArrowUpDown
          className={cn(
            "h-3 w-3",
            sortKey === sortKeyValue
              ? "text-foreground"
              : "text-muted-foreground"
          )}
        />
      </button>
    );
  }

  return (
    <>
      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as TaskStatus | "")}
          className="border rounded-md px-2 py-1.5 text-sm bg-card"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="blocked">Blocked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="border rounded-md px-2 py-1.5 text-sm bg-card"
        >
          <option value="">All priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortButton label="Task" sortKeyValue="title" />
            </TableHead>
            <TableHead>
              <SortButton label="Stage" sortKeyValue="stage" />
            </TableHead>
            <TableHead>
              <SortButton label="Status" sortKeyValue="status" />
            </TableHead>
            <TableHead>
              <SortButton label="Priority" sortKeyValue="priority" />
            </TableHead>
            <TableHead>
              <SortButton label="Due Date" sortKeyValue="due_date" />
            </TableHead>
            <TableHead>Assignee</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredTasks.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8">
                <p className="text-sm text-muted-foreground">
                  No tasks match the current filters.
                </p>
              </TableCell>
            </TableRow>
          )}
          {filteredTasks.map((task) => {
            const dueDate = task.due_date
              ? new Date(task.due_date)
              : null;
            const isOverdue =
              dueDate &&
              isPast(dueDate) &&
              task.status !== "completed";
            const stageName = task.stage_id
              ? stageMap[task.stage_id]?.name ?? "Unknown"
              : "-";

            return (
              <TableRow
                key={task.id}
                className="cursor-pointer"
                onClick={() => setSelectedTask(task)}
              >
                <TableCell>
                  <div className="flex items-center gap-2">
                    {statusIcons[task.status]}
                    <span className="text-sm font-medium">{task.title}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-sm">{stageName}</span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="secondary"
                    className={cn(
                      "text-[10px] capitalize",
                      statusColors[task.status]
                    )}
                  >
                    {task.status.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell>
                  {task.priority ? (
                    <Badge
                      variant="secondary"
                      className={cn(
                        "text-[10px] capitalize",
                        priorityColors[task.priority]
                      )}
                    >
                      {task.priority}
                    </Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">-</span>
                  )}
                </TableCell>
                <TableCell>
                  {dueDate ? (
                    <span
                      className={cn(
                        "text-sm",
                        isOverdue && "text-red-600 font-medium"
                      )}
                    >
                      {format(dueDate, "MMM d, yyyy")}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">-</span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {task.assignee_id
                      ? task.assignee_id.slice(0, 8) + "..."
                      : "-"}
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {/* Task detail panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          pipelineId={pipelineId}
          stages={stageList}
          open={!!selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </>
  );
}
