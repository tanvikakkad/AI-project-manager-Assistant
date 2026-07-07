import type { SelectHTMLAttributes } from "react";
import styles from "./Select.module.css";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, ...rest }: SelectProps) {
  const classes = [styles.select, className].filter(Boolean).join(" ");
  return <select className={classes} {...rest} />;
}
