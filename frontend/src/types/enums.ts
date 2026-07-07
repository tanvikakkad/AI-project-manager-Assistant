/** Mirrors backend `app/core/enums.py` — the single source of this vocabulary
 * on the frontend. Values must stay byte-for-byte identical to the backend. */

export const TaskStatus = {
  TODO: "TODO",
  IN_PROGRESS: "IN_PROGRESS",
  DONE: "DONE",
} as const;
export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export const TaskPriority = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  URGENT: "URGENT",
} as const;
export type TaskPriority = (typeof TaskPriority)[keyof typeof TaskPriority];

export const ProcessingStatus = {
  PENDING: "PENDING",
  PROCESSING: "PROCESSING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
} as const;
export type ProcessingStatus = (typeof ProcessingStatus)[keyof typeof ProcessingStatus];
