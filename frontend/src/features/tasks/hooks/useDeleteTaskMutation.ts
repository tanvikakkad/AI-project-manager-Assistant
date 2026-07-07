import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteTask } from "../../../api/tasks.api";
import { TASKS_QUERY_KEY } from "./useTasksQuery";

export function useDeleteTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
    },
  });
}
