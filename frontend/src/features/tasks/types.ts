import type { TaskPriority, TaskStatus } from "../../types/enums";

/** Mirrors backend `TaskRead` exactly (snake_case) — no client-side field
 * mapping layer, since the wire shape is the simplest source of truth. */
export interface Task {
  id: string;
  meeting_id: string;
  description: string;
  owner: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  source_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskFilters {
  owner?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
}

/** Mirrors backend `TaskUpdate` — only set fields are sent (partial update). */
export interface TaskUpdatePayload {
  description?: string;
  owner?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
}
