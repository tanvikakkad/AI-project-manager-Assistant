import type { CSSProperties } from "react";
import styles from "./Spinner.module.css";

interface SpinnerProps {
  size?: number;
  label?: string;
}

export function Spinner({ size = 20, label = "Loading" }: SpinnerProps) {
  const style = { "--spinner-size": `${size}px` } as CSSProperties;
  return <span className={styles.spinner} style={style} role="status" aria-label={label} />;
}
