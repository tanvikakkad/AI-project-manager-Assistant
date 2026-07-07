import { useMutation } from "@tanstack/react-query";
import { extractMeetingPreview } from "../../../api/meetings.api";

/** No cache invalidation here — nothing is persisted by this step. */
export function useExtractPreviewMutation() {
  return useMutation({
    mutationFn: extractMeetingPreview,
  });
}
