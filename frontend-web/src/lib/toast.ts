import { toast as sonnerToast } from 'sonner';

export interface ToastOptions {
  id?: string | number;
  duration?: number;
  description?: string;
}

export const toast = {
  success: (message: string, options?: ToastOptions) => {
    return sonnerToast.success(message, {
      id: options?.id,
      duration: options?.duration,
      description: options?.description,
    });
  },

  error: (message: string, options?: ToastOptions) => {
    return sonnerToast.error(message, {
      id: options?.id,
      duration: options?.duration,
      description: options?.description,
    });
  },

  warning: (message: string, options?: ToastOptions) => {
    return sonnerToast.warning(message, {
      id: options?.id,
      duration: options?.duration,
      description: options?.description,
    });
  },

  info: (message: string, options?: ToastOptions) => {
    return sonnerToast.info(message, {
      id: options?.id,
      duration: options?.duration,
      description: options?.description,
    });
  },

  loading: (message: string, options?: ToastOptions) => {
    return sonnerToast.loading(message, {
      id: options?.id,
      duration: options?.duration,
      description: options?.description,
    });
  },

  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId);
  },

  promise: <T>(
    promise: Promise<T>,
    {
      loading,
      success,
      error,
    }: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    }
  ) => {
    return sonnerToast.promise(promise, {
      loading,
      success,
      error,
    });
  },
};

// For backward compatibility with existing useToast hook
export function useToast() {
  return {
    toast,
    dismiss: toast.dismiss,
  };
}