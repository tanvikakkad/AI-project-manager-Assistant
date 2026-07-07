import { TaskPriority, TaskStatus } from "../types/enums";

/** Human-readable labels — the only place UI copy for these enums lives. */
export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  [TaskStatus.TODO]: "To Do",
  [TaskStatus.IN_PROGRESS]: "In Progress",
  [TaskStatus.DONE]: "Done",
};

export const TASK_PRIORITY_LABELS: Record<TaskPriority, string> = {
  [TaskPriority.LOW]: "Low",
  [TaskPriority.MEDIUM]: "Medium",
  [TaskPriority.HIGH]: "High",
  [TaskPriority.URGENT]: "Urgent",
};

export const TASK_STATUS_OPTIONS = Object.values(TaskStatus);
export const TASK_PRIORITY_OPTIONS = Object.values(TaskPriority);
