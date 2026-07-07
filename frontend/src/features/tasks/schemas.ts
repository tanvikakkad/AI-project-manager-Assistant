import { z } from "zod";
import { TaskPriority, TaskStatus } from "../../types/enums";

const PRIORITY_VALUES = Object.values(TaskPriority) as [TaskPriority, ...TaskPriority[]];
const STATUS_VALUES = Object.values(TaskStatus) as [TaskStatus, ...TaskStatus[]];

const MAX_DESCRIPTION_LENGTH = 2000;
const MAX_OWNER_LENGTH = 255;

export const taskEditSchema = z.object({
  description: z
    .string()
    .min(1, "Description is required.")
    .max(MAX_DESCRIPTION_LENGTH, "Description is too long."),
  owner: z.string().max(MAX_OWNER_LENGTH, "Owner name is too long.").optional(),
  priority: z.enum(PRIORITY_VALUES),
  status: z.enum(STATUS_VALUES),
  due_date: z.string().optional(),
});

export type TaskEditFormValues = z.infer<typeof taskEditSchema>;
