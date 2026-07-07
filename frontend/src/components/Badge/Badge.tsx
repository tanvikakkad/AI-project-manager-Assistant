import type { CSSProperties } from "react";
import styles from "./Badge.module.css";

interface BadgeProps {
  label: string;
  /** A CSS color value (typically a `var(--color-...)` theme token). */
  color: string;
}

/** Generic dot-and-label pill. Feature-specific color mapping (status/priority)
 * lives in `features/tasks/components`, not here. Kept subtle/muted by design
 * — no full-saturation fills — so a table full of badges still reads as one
 * clean product, not a "colorful dashboard". */
export function Badge({ label, color }: BadgeProps) {
  const style = { "--badge-color": color } as CSSProperties;
  return (
    <span className={styles.badge} style={style}>
      <span className={styles.dot} aria-hidden="true" />
      {label}
    </span>
  );
}
