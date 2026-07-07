import { Badge } from "../../../components/Badge/Badge";
import { TASK_STATUS_LABELS } from "../../../constants/taskLabels";
import { TaskStatus } from "../../../types/enums";

const STATUS_COLOR_VARS: Record<TaskStatus, string> = {
  [TaskStatus.TODO]: "var(--color-status-todo)",
  [TaskStatus.IN_PROGRESS]: "var(--color-status-in-progress)",
  [TaskStatus.DONE]: "var(--color-status-done)",
};

export function StatusBadge({ status }: { status: TaskStatus }) {
  return <Badge label={TASK_STATUS_LABELS[status]} color={STATUS_COLOR_VARS[status]} />;
}
