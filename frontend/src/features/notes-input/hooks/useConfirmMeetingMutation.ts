import { useMutation, useQueryClient } from "@tanstack/react-query";
import { confirmMeeting } from "../../../api/meetings.api";
import { TASKS_QUERY_KEY } from "../../tasks/hooks/useTasksQuery";

export function useConfirmMeetingMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: confirmMeeting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
    },
  });
}
