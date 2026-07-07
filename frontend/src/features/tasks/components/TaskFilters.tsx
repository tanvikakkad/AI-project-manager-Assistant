import { useMemo } from "react";
import { Select } from "../../../components/Select/Select";
import { TASK_PRIORITY_LABELS, TASK_STATUS_LABELS } from "../../../constants/taskLabels";
import { TaskPriority, TaskStatus } from "../../../types/enums";
import type { Task, TaskFilters as TaskFiltersValue } from "../types";
import styles from "./TaskFilters.module.css";

interface TaskFiltersProps {
  filters: TaskFiltersValue;
  onChange: (filters: TaskFiltersValue) => void;
  /** Unfiltered task list, used only to derive the set of known owners. */
  allTasks: Task[];
}

const ALL_VALUE = "";

export function TaskFilters({ filters, onChange, allTasks }: TaskFiltersProps) {
  const ownerOptions = useMemo(() => {
    const owners = new Set<string>();
    for (const task of allTasks) {
      if (task.owner) {
        owners.add(task.owner);
      }
    }
    return Array.from(owners).sort();
  }, [allTasks]);

  return (
    <div className={styles.filters}>
      <Select
        aria-label="Filter by owner"
        value={filters.owner ?? ALL_VALUE}
        onChange={(event) => onChange({ ...filters, owner: event.target.value || undefined })}
      >
        <option value={ALL_VALUE}>All owners</option>
        {ownerOptions.map((owner) => (
          <option key={owner} value={owner}>
            {owner}
          </option>
        ))}
      </Select>

      <Select
        aria-label="Filter by status"
        value={filters.status ?? ALL_VALUE}
        onChange={(event) =>
          onChange({
            ...filters,
            status: (event.target.value || undefined) as TaskStatus | undefined,
          })
        }
      >
        <option value={ALL_VALUE}>All statuses</option>
        {Object.values(TaskStatus).map((status) => (
          <option key={status} value={status}>
            {TASK_STATUS_LABELS[status]}
          </option>
        ))}
      </Select>

      <Select
        aria-label="Filter by priority"
        value={filters.priority ?? ALL_VALUE}
        onChange={(event) =>
          onChange({
            ...filters,
            priority: (event.target.value || undefined) as TaskPriority | undefined,
          })
        }
      >
        <option value={ALL_VALUE}>All priorities</option>
        {Object.values(TaskPriority).map((priority) => (
          <option key={priority} value={priority}>
            {TASK_PRIORITY_LABELS[priority]}
          </option>
        ))}
      </Select>
    </div>
  );
}
