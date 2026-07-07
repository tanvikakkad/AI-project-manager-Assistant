import type { ReactNode } from "react";
import styles from "./Layout.module.css";

const APP_TITLE = "Mini AI Project Manager Assistant";
const APP_MARK = "AI";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <span className={styles.logo} aria-hidden="true">
          {APP_MARK}
        </span>
        <h1 className={styles.title}>{APP_TITLE}</h1>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
