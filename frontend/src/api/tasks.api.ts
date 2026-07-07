import { axiosClient } from "./axiosClient";
import type { ApiResponse } from "./apiTypes";
import { API_ROUTES } from "../constants/apiRoutes";
import type { Task, TaskFilters, TaskUpdatePayload } from "../features/tasks/types";

export async function fetchTasks(filters: TaskFilters): Promise<Task[]> {
  const response = await axiosClient.get<ApiResponse<Task[]>>(API_ROUTES.tasks, {
    params: filters,
  });
  return response.data.data;
}

export async function updateTask(taskId: string, payload: TaskUpdatePayload): Promise<Task> {
  const response = await axiosClient.patch<ApiResponse<Task>>(
    `${API_ROUTES.tasks}/${taskId}`,
    payload,
  );
  return response.data.data;
}

export async function deleteTask(taskId: string): Promise<void> {
  await axiosClient.delete(`${API_ROUTES.tasks}/${taskId}`);
}

/** Builds the CSV download URL for the given filters. The response is sent
 * with `Content-Disposition: attachment`, so a plain navigation triggers a
 * download without leaving the page — no blob-handling needed. */
export function buildExportCsvUrl(filters: TaskFilters): string {
  const params = new URLSearchParams();
  if (filters.owner) params.set("owner", filters.owner);
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);

  const query = params.toString();
  const baseUrl = axiosClient.defaults.baseURL ?? "";
  return `${baseUrl}${API_ROUTES.tasks}/export/csv${query ? `?${query}` : ""}`;
}
