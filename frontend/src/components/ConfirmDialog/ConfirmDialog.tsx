import { Button } from "../Button/Button";
import styles from "./ConfirmDialog.module.css";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  isConfirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  isConfirming = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" aria-label={title}>
      <div className={styles.dialog}>
        <h2 className={styles.heading}>{title}</h2>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <Button variant="secondary" onClick={onCancel} disabled={isConfirming}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={isConfirming}>
            {isConfirming ? "Deleting…" : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
