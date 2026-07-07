import { useState } from "react";
import type { MeetingExtractionPreview } from "../types";
import { ExtractionReviewPanel } from "./ExtractionReviewPanel";
import { NotesInputForm } from "./NotesInputForm";
import styles from "./NotesInputSection.module.css";

/** Orchestrates the human-in-the-loop workflow:
 * Notes -> AI extraction (preview, unsaved) -> user review -> confirm (saved). */
export function NotesInputSection() {
  const [preview, setPreview] = useState<MeetingExtractionPreview | null>(null);

  return (
    <section className={styles.section}>
      {preview ? (
        <ExtractionReviewPanel
          preview={preview}
          onSaved={() => setPreview(null)}
          onCancel={() => setPreview(null)}
        />
      ) : (
        <NotesInputForm onPreview={setPreview} />
      )}
    </section>
  );
}
