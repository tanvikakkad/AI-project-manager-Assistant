import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "../../../components/Button/Button";
import { Select } from "../../../components/Select/Select";
import { TextArea } from "../../../components/TextArea/TextArea";
import { TextInput } from "../../../components/TextInput/TextInput";
import { TASK_PRIORITY_LABELS, TASK_STATUS_LABELS } from "../../../constants/taskLabels";
import { TaskPriority, TaskStatus } from "../../../types/enums";
import { taskEditSchema, type TaskEditFormValues } from "../schemas";
import type { Task } from "../types";
import styles from "./TaskEditDialog.module.css";

interface TaskEditDialogProps {
  task: Task;
  isSaving: boolean;
  onSave: (values: TaskEditFormValues) => void;
  onClose: () => void;
}

export function TaskEditDialog({ task, isSaving, onSave, onClose }: TaskEditDialogProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TaskEditFormValues>({
    resolver: zodResolver(taskEditSchema),
    defaultValues: {
      description: task.description,
      owner: task.owner ?? "",
      priority: task.priority,
      status: task.status,
      due_date: task.due_date ?? "",
    },
  });

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" aria-label="Edit task">
      <div className={styles.dialog}>
        <h2 className={styles.heading}>Edit task</h2>
        <form onSubmit={handleSubmit(onSave)} className={styles.form} noValidate>
          <label className={styles.field}>
            <span>Description</span>
            <TextArea rows={3} {...register("description")} />
            {errors.description ? (
              <span className={styles.error}>{errors.description.message}</span>
            ) : null}
          </label>

          <label className={styles.field}>
            <span>Owner</span>
            <TextInput type="text" {...register("owner")} />
            {errors.owner ? <span className={styles.error}>{errors.owner.message}</span> : null}
          </label>

          <div className={styles.grid}>
            <label className={styles.field}>
              <span>Priority</span>
              <Select {...register("priority")}>
                {Object.values(TaskPriority).map((priority) => (
                  <option key={priority} value={priority}>
                    {TASK_PRIORITY_LABELS[priority]}
                  </option>
                ))}
              </Select>
            </label>

            <label className={styles.field}>
              <span>Status</span>
              <Select {...register("status")}>
                {Object.values(TaskStatus).map((status) => (
                  <option key={status} value={status}>
                    {TASK_STATUS_LABELS[status]}
                  </option>
                ))}
              </Select>
            </label>
          </div>

          <label className={styles.field}>
            <span>Due date</span>
            <TextInput type="date" {...register("due_date")} />
          </label>

          <div className={styles.actions}>
            <Button variant="secondary" type="button" onClick={onClose} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
