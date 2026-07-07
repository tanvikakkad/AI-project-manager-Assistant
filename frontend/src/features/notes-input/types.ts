import type { ProcessingStatus } from "../../types/enums";
import type { Task } from "../tasks/types";

/** Mirrors backend `MeetingRead` exactly (snake_case). */
export interface Meeting {
  id: string;
  title: string;
  meeting_date: string;
  meeting_time: string;
  raw_notes: string;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}

export interface MeetingWithTasks extends Meeting {
  tasks: Task[];
}

/** Mirrors backend `MeetingCreate` — title/date/time are optional and
 * user-provided only, never LLM-inferred (see ARCHITECTURE.md §29). */
export interface ExtractPreviewPayload {
  title?: string;
  meeting_date?: string;
  meeting_time?: string;
  raw_notes: string;
}

/** Mirrors backend `ExtractedTaskDTO` — an AI-suggested task awaiting human
 * review. Not yet persisted; has no `id`, `status`, or timestamps. */
export interface DraftTask {
  description: string;
  owner: string | null;
  due_date: string | null;
  priority: Task["priority"];
  source_text: string | null;
}

/** Mirrors backend `MeetingExtractionPreview` — the response of the
 * extract-only step. Nothing has been saved yet. */
export interface MeetingExtractionPreview {
  title: string;
  meeting_date: string;
  meeting_time: string;
  raw_notes: string;
  tasks: DraftTask[];
}

/** Mirrors backend `MeetingConfirmRequest` — the human-reviewed task list
 * the user has confirmed should be persisted. */
export interface ConfirmMeetingPayload {
  title: string;
  meeting_date: string;
  meeting_time: string;
  raw_notes: string;
  tasks: DraftTask[];
}
