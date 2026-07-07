import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Icon rendered before the label (hidden while `isLoading`, replaced by the spinner). */
  icon?: ReactNode;
  /** Shows a spinner in place of `icon` and disables the button. */
  isLoading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  icon,
  isLoading = false,
  className,
  type = "button",
  disabled,
  children,
  ...rest
}: ButtonProps) {
  const classes = [styles.button, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} disabled={disabled || isLoading} {...rest}>
      {isLoading ? <span className={styles.spinner} aria-hidden="true" /> : icon}
      {children}
    </button>
  );
}
