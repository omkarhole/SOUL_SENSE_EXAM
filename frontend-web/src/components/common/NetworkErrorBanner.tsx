'use client';

import React, { useEffect, useState } from 'react';

import { WifiOff, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMounted } from '@/hooks/useMounted';

export const NetworkErrorBanner = () => {
  const isMounted = useMounted();
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    setIsOffline(!navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isMounted) return null;

  return (
    <AnimatePresence>
      {isOffline && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="bg-red-600 text-white py-2 px-4 flex items-center justify-center gap-3 text-sm font-medium sticky top-0 z-[100]"
        >
          <WifiOff className="h-4 w-4" />
          <span>You are currently offline. Some features may be limited.</span>
          <button
            onClick={() => setIsOffline(false)}
            className="ml-auto hover:bg-white/20 p-1 rounded-full transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
