// Luxury Royal Toast & Confirm Notification System for Haybat Al Sultan

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

export interface ConfirmDialogOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
}

type ToastListener = (toasts: ToastItem[]) => void;
type ConfirmListener = (dialog: (ConfirmDialogOptions & { resolve: (val: boolean) => void }) | null) => void;

class NotificationManager {
  private toasts: ToastItem[] = [];
  private toastListeners: Set<ToastListener> = new Set();
  private confirmListener: ConfirmListener | null = null;

  subscribeToasts(listener: ToastListener) {
    this.toastListeners.add(listener);
    listener([...this.toasts]);
    return () => {
      this.toastListeners.delete(listener);
    };
  }

  subscribeConfirm(listener: ConfirmListener) {
    this.confirmListener = listener;
    return () => {
      if (this.confirmListener === listener) {
        this.confirmListener = null;
      }
    };
  }

  private notifyToasts() {
    this.toastListeners.forEach(listener => listener([...this.toasts]));
  }

  show(type: ToastType, message: string, title?: string, duration: number = 4000): string {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastItem = { id, type, title, message, duration };
    this.toasts = [newToast, ...this.toasts.slice(0, 4)]; // keep max 5 toasts
    this.notifyToasts();

    if (duration > 0) {
      setTimeout(() => {
        this.dismiss(id);
      }, duration);
    }
    return id;
  }

  dismiss(id: string) {
    this.toasts = this.toasts.filter(t => t.id !== id);
    this.notifyToasts();
  }

  clear() {
    this.toasts = [];
    this.notifyToasts();
  }

  confirm(options: ConfirmDialogOptions | string): Promise<boolean> {
    const opts: ConfirmDialogOptions = typeof options === 'string' ? { message: options } : options;
    return new Promise(resolve => {
      if (this.confirmListener) {
        this.confirmListener({
          ...opts,
          resolve: (val: boolean) => {
            if (this.confirmListener) {
              this.confirmListener(null);
            }
            resolve(val);
          }
        });
      } else {
        // Fallback if component not yet mounted
        const fallback = window.confirm(opts.message);
        resolve(fallback);
      }
    });
  }
}

export const notificationManager = new NotificationManager();

export const toast = {
  success: (message: string, title?: string, duration?: number) =>
    notificationManager.show('success', message, title || 'تمت العملية بنجاح', duration),
  error: (message: string, title?: string, duration?: number) =>
    notificationManager.show('error', message, title || 'تنبيه خطأ', duration || 5000),
  warning: (message: string, title?: string, duration?: number) =>
    notificationManager.show('warning', message, title || 'تنبيه هام', duration),
  info: (message: string, title?: string, duration?: number) =>
    notificationManager.show('info', message, title || 'معلومة', duration),
  confirm: (options: ConfirmDialogOptions | string) =>
    notificationManager.confirm(options),
  dismiss: (id: string) => notificationManager.dismiss(id),
  clear: () => notificationManager.clear()
};

export default toast;
