import { axiosClient } from "./axiosClient";
import type { ApiResponse } from "./apiTypes";
import { API_ROUTES } from "../constants/apiRoutes";
import type {
  ConfirmMeetingPayload,
  ExtractPreviewPayload,
  MeetingExtractionPreview,
  MeetingWithTasks,
} from "../features/notes-input/types";

/** Runs AI extraction only — nothing is persisted. */
export async function extractMeetingPreview(
  payload: ExtractPreviewPayload,
): Promise<MeetingExtractionPreview> {
  const response = await axiosClient.post<ApiResponse<MeetingExtractionPreview>>(
    `${API_ROUTES.meetings}/extract`,
    payload,
  );
  return response.data.data;
}

/** Persists the meeting and exactly the (possibly edited) tasks the user confirmed. */
export async function confirmMeeting(payload: ConfirmMeetingPayload): Promise<MeetingWithTasks> {
  const response = await axiosClient.post<ApiResponse<MeetingWithTasks>>(
    API_ROUTES.meetings,
    payload,
  );
  return response.data.data;
}
