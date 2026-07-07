import type { ReactNode } from "react";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className={styles.emptyState}>
      <span className={styles.title}>{title}</span>
      {description ? <p>{description}</p> : null}
      {action}
    </div>
  );
}
