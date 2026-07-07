import { useState } from "react";
import { getApiErrorMessage } from "../../../api/getApiErrorMessage";
import { ConfirmDialog } from "../../../components/ConfirmDialog/ConfirmDialog";
import { EmptyState } from "../../../components/EmptyState/EmptyState";
import { Spinner } from "../../../components/Spinner/Spinner";
import { useToast } from "../../../components/Toast/ToastContext";
import { useDeleteTaskMutation } from "../hooks/useDeleteTaskMutation";
import { useTasksQuery } from "../hooks/useTasksQuery";
import { useUpdateTaskMutation } from "../hooks/useUpdateTaskMutation";
import type { TaskEditFormValues } from "../schemas";
import type { Task, TaskFilters as TaskFiltersValue } from "../types";
import { ExportCsvButton } from "./ExportCsvButton";
import { TaskEditDialog } from "./TaskEditDialog";
import { TaskFilters } from "./TaskFilters";
import { TaskTable } from "./TaskTable";
import styles from "./TasksSection.module.css";

export function TasksSection() {
  const [filters, setFilters] = useState<TaskFiltersValue>({});
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingTask, setDeletingTask] = useState<Task | null>(null);
  const { showToast } = useToast();

  // Unfiltered fetch, used to derive the owner dropdown and the total task count.
  const allTasksQuery = useTasksQuery({});
  const filteredTasksQuery = useTasksQuery(filters);
  const updateTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();

  const totalTaskCount = allTasksQuery.data?.length ?? 0;
  const hasNoTasksAtAll = !allTasksQuery.isLoading && !allTasksQuery.isError && totalTaskCount === 0;

  async function handleSave(values: TaskEditFormValues) {
    if (!editingTask) {
      return;
    }
    try {
      await updateTaskMutation.mutateAsync({
        taskId: editingTask.id,
        payload: {
          description: values.description,
          owner: values.owner || null,
          priority: values.priority,
          status: values.status,
          due_date: values.due_date || null,
        },
      });
      showToast("Task updated.", "success");
      setEditingTask(null);
    } catch (error) {
      showToast(getApiErrorMessage(error), "error");
    }
  }

  async function handleConfirmDelete() {
    if (!deletingTask) {
      return;
    }
    try {
      await deleteTaskMutation.mutateAsync(deletingTask.id);
      showToast("Task deleted.", "success");
      setDeletingTask(null);
    } catch (error) {
      showToast(getApiErrorMessage(error), "error");
    }
  }

  return (
    <section className={styles.section}>
      <div className={styles.headerRow}>
        <h2 className={styles.heading}>
          Tasks
          {!allTasksQuery.isLoading && !allTasksQuery.isError ? (
            <span className={styles.count}>{totalTaskCount}</span>
          ) : null}
        </h2>
        <div className={styles.controls}>
          <TaskFilters
            filters={filters}
            onChange={setFilters}
            allTasks={allTasksQuery.data ?? []}
          />
          <ExportCsvButton filters={filters} />
        </div>
      </div>

      {filteredTasksQuery.isLoading ? (
        <div className={styles.loading}>
          <Spinner />
          <span>Loading tasks…</span>
        </div>
      ) : filteredTasksQuery.isError ? (
        <EmptyState
          title="Couldn't load tasks"
          description={getApiErrorMessage(filteredTasksQuery.error)}
        />
      ) : hasNoTasksAtAll ? (
        <EmptyState
          title="No tasks yet"
          description="Paste meeting notes above and click Extract Tasks to create your first ones."
        />
      ) : (
        <TaskTable
          tasks={filteredTasksQuery.data ?? []}
          onEdit={setEditingTask}
          onDelete={setDeletingTask}
        />
      )}

      {editingTask ? (
        <TaskEditDialog
          task={editingTask}
          isSaving={updateTaskMutation.isPending}
          onSave={handleSave}
          onClose={() => setEditingTask(null)}
        />
      ) : null}

      {deletingTask ? (
        <ConfirmDialog
          title="Delete task"
          message={`Delete "${deletingTask.description}"? This cannot be undone.`}
          confirmLabel="Delete"
          isConfirming={deleteTaskMutation.isPending}
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeletingTask(null)}
        />
      ) : null}
    </section>
  );
}
