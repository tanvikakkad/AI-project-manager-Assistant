import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateTask } from "../../../api/tasks.api";
import type { TaskUpdatePayload } from "../types";
import { TASKS_QUERY_KEY } from "./useTasksQuery";

interface UpdateTaskArgs {
  taskId: string;
  payload: TaskUpdatePayload;
}

export function useUpdateTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, payload }: UpdateTaskArgs) => updateTask(taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
    },
  });
}
