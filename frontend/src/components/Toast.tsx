import React, { useEffect, useState } from 'react';
import { Toast as ToastType, ToastType as ToastVariant } from '../contexts/ToastContext';

interface ToastProps {
  toast: ToastType;
  onDismiss: (id: string) => void;
}

const ICONS: Record<ToastVariant, string> = {
  success: '\u2713', // checkmark
  error: '\u2717',   // X mark
  warning: '\u26A0', // warning triangle
  info: '\u2139',    // info circle
};

export function Toast({ toast, onDismiss }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Start exit animation before removal
    if (toast.duration && toast.duration > 0) {
      const exitTimer = setTimeout(() => {
        setIsExiting(true);
      }, toast.duration - 300); // Start exit 300ms before removal

      return () => clearTimeout(exitTimer);
    }
  }, [toast.duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => onDismiss(toast.id), 300);
  };

  return (
    <div
      className={`toast toast-${toast.type} ${isExiting ? 'toast-exit' : ''}`}
      role="alert"
      aria-live="polite"
    >
      <span className="toast-icon" aria-hidden="true">
        {ICONS[toast.type]}
      </span>
      <span className="toast-message">{toast.message}</span>
      <button
        className="toast-dismiss"
        onClick={handleDismiss}
        aria-label="Dismiss notification"
      >
        {'\u00D7'}
      </button>
    </div>
  );
}

export default Toast;
