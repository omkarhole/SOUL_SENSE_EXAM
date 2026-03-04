'use client';

import { useEffect, useState } from 'react';
import { networkMonitor, NetworkState } from '@/lib/offline/network';
import { syncQueue } from '@/lib/offline/syncQueue';
import { useMounted } from '@/hooks/useMounted';
import { WifiOff, Wifi, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export function OfflineBanner() {
  const isMounted = useMounted();
  const [networkState, setNetworkState] = useState<NetworkState>(networkMonitor.getCurrentState());
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (!isMounted) return;
    const unsubscribe = networkMonitor.subscribe((state) => {
      setNetworkState(state);

      if (state.isOnline) {
        syncQueue.processQueue().then(() => {
          updateStats();
        });
      }
    });

    updateStats();

    const interval = setInterval(updateStats, 5000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const updateStats = async () => {
    const stats = await syncQueue.getStats();
    setPendingCount(stats.totalPending);
    setSyncing(syncQueue.isProcessingQueue());
  };

  if (!isMounted || (networkState.isOnline && pendingCount === 0)) {
    return null;
  }

  return (
    <div
      className={`
      fixed top-0 left-0 right-0 z-50
      ${networkState.isOnline ? 'bg-green-50 dark:bg-green-950 border-b-2 border-green-200 dark:border-green-800' : 'bg-orange-50 dark:bg-orange-950 border-b-2 border-orange-200 dark:border-orange-800'}
      transition-colors duration-300
    `}
    >
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-center gap-3 text-sm">
          {networkState.isOnline ? (
            <>
              <Wifi className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-green-800 dark:text-green-200 font-medium">Back online</span>
              {pendingCount > 0 && (
                <>
                  <span className="text-green-600 dark:text-green-400">•</span>
                  {syncing ? (
                    <>
                      <RefreshCw className="w-4 h-4 text-green-600 dark:text-green-400 animate-spin" />
                      <span className="text-green-700 dark:text-green-300">
                        Syncing {pendingCount} item{pendingCount !== 1 ? 's' : ''}...
                      </span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-green-700 dark:text-green-300">
                        {pendingCount} item{pendingCount !== 1 ? 's' : ''} synced
                      </span>
                    </>
                  )}
                </>
              )}
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              <span className="text-orange-800 dark:text-orange-200 font-medium">
                You&apos;re offline
              </span>
              {pendingCount > 0 && (
                <>
                  <span className="text-orange-600 dark:text-orange-400">•</span>
                  <AlertCircle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                  <span className="text-orange-700 dark:text-orange-300">
                    {pendingCount} change{pendingCount !== 1 ? 's' : ''} will sync when you
                    reconnect
                  </span>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
