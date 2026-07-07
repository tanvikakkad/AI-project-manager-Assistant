import { z } from "zod";

const MAX_RAW_NOTES_LENGTH = 20_000;
const MAX_TITLE_LENGTH = 255;

const NOTES_REQUIRED_MESSAGE = "Please paste some meeting notes.";
const NOTES_TOO_LONG_MESSAGE = "Notes are too long.";
const TITLE_TOO_LONG_MESSAGE = "Title is too long.";
const DATE_IN_FUTURE_MESSAGE = "Meeting date cannot be in the future.";
const TIME_IN_FUTURE_MESSAGE = "Meeting time cannot be in the future for today's date.";

/** "YYYY-MM-DD" — lexicographic string comparison matches chronological
 * order for zero-padded ISO dates, so no Date-object/timezone handling needed. */
function todayIsoDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
    now.getDate(),
  ).padStart(2, "0")}`;
}

/** "HH:MM" — matches what <input type="time"> produces. */
function nowHoursMinutes(): string {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

export const notesInputSchema = z
  .object({
    title: z.string().max(MAX_TITLE_LENGTH, TITLE_TOO_LONG_MESSAGE).optional(),
    meeting_date: z.string().optional(),
    meeting_time: z.string().optional(),
    raw_notes: z
      .string()
      .max(MAX_RAW_NOTES_LENGTH, NOTES_TOO_LONG_MESSAGE)
      .transform((value) => value.trim())
      .refine((value) => value.length > 0, NOTES_REQUIRED_MESSAGE),
  })
  .superRefine((values, ctx) => {
    const today = todayIsoDate();

    if (values.meeting_date && values.meeting_date > today) {
      ctx.addIssue({ code: "custom", path: ["meeting_date"], message: DATE_IN_FUTURE_MESSAGE });
    }

    const effectiveDate = values.meeting_date || today;
    if (effectiveDate === today && values.meeting_time && values.meeting_time > nowHoursMinutes()) {
      ctx.addIssue({ code: "custom", path: ["meeting_time"], message: TIME_IN_FUTURE_MESSAGE });
    }
  });

export type NotesInputFormValues = z.infer<typeof notesInputSchema>;
