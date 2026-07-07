import { Button } from "../../../components/Button/Button";
import { EmptyState } from "../../../components/EmptyState/EmptyState";
import type { Task } from "../types";
import { PriorityBadge } from "./PriorityBadge";
import { StatusBadge } from "./StatusBadge";
import styles from "./TaskTable.module.css";

interface TaskTableProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

const NO_VALUE_PLACEHOLDER = "—";

function formatDueDate(dueDate: string | null): string {
  if (!dueDate) {
    return NO_VALUE_PLACEHOLDER;
  }
  return new Date(dueDate).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function TaskTable({ tasks, onEdit, onDelete }: TaskTableProps) {
  if (tasks.length === 0) {
    return (
      <EmptyState
        title="No tasks match these filters"
        description="Try clearing a filter, or paste meeting notes above to create new tasks."
      />
    );
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Description</th>
            <th>Owner</th>
            <th>Due date</th>
            <th>Priority</th>
            <th>Status</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id}>
              <td>{task.description}</td>
              <td>{task.owner ?? NO_VALUE_PLACEHOLDER}</td>
              <td>{formatDueDate(task.due_date)}</td>
              <td>
                <PriorityBadge priority={task.priority} />
              </td>
              <td>
                <StatusBadge status={task.status} />
              </td>
              <td className={styles.actions}>
                <Button variant="ghost" onClick={() => onEdit(task)}>
                  Edit
                </Button>
                <Button variant="danger" onClick={() => onDelete(task)}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
