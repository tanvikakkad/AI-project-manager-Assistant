import { useState } from "react";
import { getApiErrorMessage } from "../../../api/getApiErrorMessage";
import { Button } from "../../../components/Button/Button";
import { Select } from "../../../components/Select/Select";
import { TextInput } from "../../../components/TextInput/TextInput";
import { useToast } from "../../../components/Toast/ToastContext";
import { TASK_PRIORITY_LABELS } from "../../../constants/taskLabels";
import { TaskPriority } from "../../../types/enums";
import { useConfirmMeetingMutation } from "../hooks/useConfirmMeetingMutation";
import type { DraftTask, MeetingExtractionPreview } from "../types";
import styles from "./ExtractionReviewPanel.module.css";

interface EditableDraftTask extends DraftTask {
  key: string;
}

interface ExtractionReviewPanelProps {
  preview: MeetingExtractionPreview;
  onSaved: () => void;
  onCancel: () => void;
}

function createKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random()}`;
}

/** Human-in-the-loop review step: AI-suggested tasks are held here, in local
 * component state only, until the user explicitly confirms — nothing here
 * touches the server except the final "Save All". */
export function ExtractionReviewPanel({ preview, onSaved, onCancel }: ExtractionReviewPanelProps) {
  const { showToast } = useToast();
  const { mutateAsync, isPending } = useConfirmMeetingMutation();
  const [drafts, setDrafts] = useState<EditableDraftTask[]>(() =>
    preview.tasks.map((task) => ({ ...task, key: createKey() })),
  );
  const [attemptedSave, setAttemptedSave] = useState(false);

  function updateDraft(key: string, patch: Partial<DraftTask>) {
    setDrafts((current) => current.map((draft) => (draft.key === key ? { ...draft, ...patch } : draft)));
  }

  function removeDraft(key: string) {
    setDrafts((current) => current.filter((draft) => draft.key !== key));
  }

  const invalidKeys = new Set(
    drafts.filter((draft) => draft.description.trim().length === 0).map((draft) => draft.key),
  );

  async function handleSaveAll() {
    setAttemptedSave(true);
    if (invalidKeys.size > 0) {
      return;
    }
    try {
      const saved = await mutateAsync({
        title: preview.title,
        meeting_date: preview.meeting_date,
        meeting_time: preview.meeting_time,
        raw_notes: preview.raw_notes,
        tasks: drafts.map(({ key: _key, ...task }) => task),
      });
      showToast(`Saved ${saved.tasks.length} task(s) to "${saved.title}".`, "success");
      onSaved();
    } catch (error) {
      showToast(getApiErrorMessage(error), "error");
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.banner}>
        <strong>AI-generated suggestions — nothing has been saved yet.</strong> Review, edit, or
        remove tasks below, then confirm.
      </div>

      {drafts.length === 0 ? (
        <p className={styles.emptyMessage}>
          No tasks left to save. Cancel to go back and try different notes.
        </p>
      ) : (
        <ul className={styles.list}>
          {drafts.map((draft) => (
            <li key={draft.key} className={styles.row}>
              <label className={styles.field}>
                <span>Description</span>
                <TextInput
                  value={draft.description}
                  onChange={(event) => updateDraft(draft.key, { description: event.target.value })}
                />
                {attemptedSave && invalidKeys.has(draft.key) ? (
                  <span className={styles.error}>Description is required.</span>
                ) : null}
              </label>
              <label className={styles.field}>
                <span>Owner</span>
                <TextInput
                  value={draft.owner ?? ""}
                  onChange={(event) =>
                    updateDraft(draft.key, { owner: event.target.value || null })
                  }
                />
              </label>
              <label className={styles.field}>
                <span>Due date</span>
                <TextInput
                  type="date"
                  value={draft.due_date ?? ""}
                  onChange={(event) =>
                    updateDraft(draft.key, { due_date: event.target.value || null })
                  }
                />
              </label>
              <label className={styles.field}>
                <span>Priority</span>
                <Select
                  value={draft.priority}
                  onChange={(event) =>
                    updateDraft(draft.key, { priority: event.target.value as TaskPriority })
                  }
                >
                  {Object.values(TaskPriority).map((priority) => (
                    <option key={priority} value={priority}>
                      {TASK_PRIORITY_LABELS[priority]}
                    </option>
                  ))}
                </Select>
              </label>
              <Button
                variant="ghost"
                type="button"
                aria-label="Remove task"
                onClick={() => removeDraft(draft.key)}
              >
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}

      <div className={styles.footer}>
        <span className={styles.count}>
          {drafts.length} task{drafts.length === 1 ? "" : "s"} ready to save
        </span>
        <div className={styles.actions}>
          <Button variant="secondary" type="button" onClick={onCancel} disabled={isPending}>
            Cancel
          </Button>
          <Button type="button" onClick={handleSaveAll} isLoading={isPending}>
            Save All
          </Button>
        </div>
      </div>
    </div>
  );
}
