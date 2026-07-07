import { useCallback, useState, type ReactNode } from "react";
import { ToastContext, type ToastVariant } from "./ToastContext";
import styles from "./Toast.module.css";

interface ToastMessage {
  id: number;
  message: string;
  variant: ToastVariant;
}

const TOAST_DURATION_MS = 4000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, variant: ToastVariant = "success") => {
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, message, variant }]);
    setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, TOAST_DURATION_MS);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className={styles.viewport} role="status" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`${styles.toast} ${styles[toast.variant]}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
