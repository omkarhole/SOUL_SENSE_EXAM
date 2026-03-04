import { toast } from './toast';

export function handleApiError(error: any, fallbackMessage = 'An error occurred') {
  console.error('API Error:', error);

  let message = fallbackMessage;

  if (error?.message) {
    message = error.message;
  } else if (error?.response?.data?.message) {
    message = error.response.data.message;
  } else if (typeof error === 'string') {
    message = error;
  }

  // Don't show toast for authentication errors as they're handled by the auth system
  if (error?.status === 401) {
    return;
  }

  toast.error(message);
}

export function handleNetworkError(error: any) {
  console.error('Network Error:', error);
  toast.error('Network connection failed. Please check your internet connection.');
}

// Global error handler for unhandled promise rejections
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    handleApiError(event.reason, 'An unexpected error occurred');
  });
}