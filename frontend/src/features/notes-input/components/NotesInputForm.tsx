import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { getApiErrorMessage } from "../../../api/getApiErrorMessage";
import { Button } from "../../../components/Button/Button";
import { Spinner } from "../../../components/Spinner/Spinner";
import { TextArea } from "../../../components/TextArea/TextArea";
import { TextInput } from "../../../components/TextInput/TextInput";
import { useToast } from "../../../components/Toast/ToastContext";
import { useExtractPreviewMutation } from "../hooks/useExtractPreviewMutation";
import { notesInputSchema, type NotesInputFormValues } from "../schemas";
import type { MeetingExtractionPreview } from "../types";
import styles from "./NotesInputForm.module.css";

interface NotesInputFormProps {
  onPreview: (preview: MeetingExtractionPreview) => void;
}

const SPARKLE_ICON = (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <path
      d="M8 1.5l1.2 3.3L12.5 6l-3.3 1.2L8 10.5l-1.2-3.3L3.5 6l3.3-1.2L8 1.5z"
      fill="currentColor"
    />
    <path
      d="M13 9l.6 1.6L15 11l-1.4.6L13 13l-.6-1.4L11 11l1.4-.4L13 9z"
      fill="currentColor"
      opacity="0.7"
    />
  </svg>
);

export function NotesInputForm({ onPreview }: NotesInputFormProps) {
  const { showToast } = useToast();
  const { mutateAsync, isPending } = useExtractPreviewMutation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<NotesInputFormValues>({
    resolver: zodResolver(notesInputSchema),
    defaultValues: { title: "", meeting_date: "", meeting_time: "", raw_notes: "" },
  });

  async function onSubmit(values: NotesInputFormValues) {
    try {
      const preview = await mutateAsync({
        title: values.title || undefined,
        meeting_date: values.meeting_date || undefined,
        meeting_time: values.meeting_time || undefined,
        raw_notes: values.raw_notes,
      });
      onPreview(preview);
    } catch (error) {
      showToast(getApiErrorMessage(error), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
      <div>
        <h2 className={styles.heading}>Extract tasks from meeting notes</h2>
        <p className={styles.subheading}>
          Paste raw notes below — the AI proposes tasks for you to review before anything is saved.
        </p>
      </div>

      <div className={styles.metaRow}>
        <label className={styles.field}>
          <span>Meeting title (optional)</span>
          <TextInput type="text" placeholder="Enter meeting title..." {...register("title")} />
          {errors.title ? <span className={styles.error}>{errors.title.message}</span> : null}
        </label>
        <label className={styles.field}>
          <span>Date (optional)</span>
          <TextInput type="date" max={new Date().toISOString().slice(0, 10)} {...register("meeting_date")} />
          {errors.meeting_date ? (
            <span className={styles.error}>{errors.meeting_date.message}</span>
          ) : null}
        </label>
        <label className={styles.field}>
          <span>Time (optional)</span>
          <TextInput type="time" {...register("meeting_time")} />
          {errors.meeting_time ? (
            <span className={styles.error}>{errors.meeting_time.message}</span>
          ) : null}
        </label>
      </div>

      <label className={styles.field}>
        <span>Meeting notes or task descriptions</span>
        <TextArea
          rows={8}
          placeholder="Paste your meeting notes here…"
          disabled={isPending}
          {...register("raw_notes")}
        />
        {errors.raw_notes ? (
          <span className={styles.error}>{errors.raw_notes.message}</span>
        ) : null}
      </label>

      <div className={styles.footer}>
        {isPending ? (
          <span className={styles.progress}>
            <Spinner size={16} />
            AI is extracting tasks…
          </span>
        ) : (
          <span />
        )}
        <Button type="submit" size="lg" icon={SPARKLE_ICON} isLoading={isPending}>
          {isPending ? "Extracting…" : "Extract Tasks"}
        </Button>
      </div>
    </form>
  );
}
