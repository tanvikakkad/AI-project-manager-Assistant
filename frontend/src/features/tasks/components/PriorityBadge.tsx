import { Badge } from "../../../components/Badge/Badge";
import { TASK_PRIORITY_LABELS } from "../../../constants/taskLabels";
import { TaskPriority } from "../../../types/enums";

const PRIORITY_COLOR_VARS: Record<TaskPriority, string> = {
  [TaskPriority.LOW]: "var(--color-priority-low)",
  [TaskPriority.MEDIUM]: "var(--color-priority-medium)",
  [TaskPriority.HIGH]: "var(--color-priority-high)",
  [TaskPriority.URGENT]: "var(--color-priority-urgent)",
};

export function PriorityBadge({ priority }: { priority: TaskPriority }) {
  return <Badge label={TASK_PRIORITY_LABELS[priority]} color={PRIORITY_COLOR_VARS[priority]} />;
}
