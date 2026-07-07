import { useQuery } from "@tanstack/react-query";
import { fetchTasks } from "../../../api/tasks.api";
import type { TaskFilters } from "../types";

export const TASKS_QUERY_KEY = "tasks";

export function useTasksQuery(filters: TaskFilters) {
  return useQuery({
    queryKey: [TASKS_QUERY_KEY, filters],
    queryFn: () => fetchTasks(filters),
  });
}
